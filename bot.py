import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.exc import NoResultFound
from cryptography.fernet import Fernet
import ccxt

from database import create_tables, SessionLocal
from models import User, APIKey
from settings import BOT_TOKEN, OWNER_ID, FERNET_KEY

# إنشاء الجداول قبل بدء البوت
create_tables()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
fernet = Fernet(FERNET_KEY.encode())

# قوائم المستخدمين
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="تسجيل/تعديل بيانات التداول")],
        [KeyboardButton(text="ابدأ استثمار"), KeyboardButton(text="استثمار وهمي")],
        [KeyboardButton(text="كشف حساب عن فترة"), KeyboardButton(text="حالة السوق")],
        [KeyboardButton(text="ايقاف الاستثمار")],
        [KeyboardButton(text="/help")]
    ],
    resize_keyboard=True
)

owner_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="تعديل نسبة ربح البوت"), KeyboardButton(text="عدد المستخدمين")],
        [KeyboardButton(text="عدد المستخدمين أونلاين"), KeyboardButton(text="تقارير الاستثمار")],
        [KeyboardButton(text="حالة البوت البرمجية")],
        [KeyboardButton(text="/help"), KeyboardButton(text="/start")]
    ],
    resize_keyboard=True
)

# FSM للحوار مع تسجيل API
class TradingDataStates(StatesGroup):
    waiting_for_exchange = State()
    waiting_for_api_key = State()
    waiting_for_api_secret = State()
    waiting_for_passphrase = State()

# ---- دوال مساعدة ----
def encrypt_text(text: str) -> str:
    return fernet.encrypt(text.encode()).decode()

def decrypt_text(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()

async def verify_api_key(exchange_name, api_key, api_secret, passphrase=None):
    """تحقق من صحة API key عن طريق ccxt."""
    try:
        exchange_class = getattr(ccxt, exchange_name)
    except AttributeError:
        return False, f"المنصة {exchange_name} غير مدعومة."

    try:
        params = {}
        if passphrase:
            params['password'] = passphrase

        exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            **params
        })

        # نطلب بيانات بسيطة (مثلاً رصيد المحفظة) كاختبار
        if hasattr(exchange, 'fetch_balance'):
            await asyncio.to_thread(exchange.load_markets)
            balance = await asyncio.to_thread(exchange.fetch_balance)
            # إذا جت استجابة بدون استثناء نعتبر المفتاح صحيح
            return True, "تم التحقق من المفتاح بنجاح."
        else:
            return False, "المنصة لا تدعم استعلام الرصيد للتحقق."
    except Exception as e:
        return False, f"خطأ في التحقق: {str(e)}"

# ----- أوامر البوت -----

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.answer("أهلاً مالك البوت!", reply_markup=owner_keyboard)
    else:
        await message.answer("أهلاً! البوت يعمل بنجاح.", reply_markup=user_keyboard)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "أوامر المستخدم:\n"
        "- تسجيل/تعديل بيانات التداول\n"
        "- ابدأ استثمار\n"
        "- استثمار وهمي\n"
        "- كشف حساب عن فترة\n"
        "- حالة السوق\n"
        "- ايقاف الاستثمار\n\n"
        "أوامر المدير:\n"
        "- تعديل نسبة ربح البوت\n"
        "- عدد المستخدمين\n"
        "- عدد المستخدمين أونلاين\n"
        "- تقارير الاستثمار\n"
        "- حالة البوت البرمجية"
    )
    await message.reply(help_text)

# ---- تسجيل/تعديل بيانات التداول ----
@dp.message(Text("تسجيل/تعديل بيانات التداول"))
async def trading_data_start(message: types.Message, state: FSMContext):
    await message.answer("اختر المنصة (مثلاً: binance, kucoin, coinbase):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(TradingDataStates.waiting_for_exchange)

@dp.message(TradingDataStates.waiting_for_exchange)
async def process_exchange(message: types.Message, state: FSMContext):
    exchange = message.text.strip().lower()
    await state.update_data(exchange=exchange)
    await message.answer("أدخل مفتاح API الخاص بالمنصة:")
    await state.set_state(TradingDataStates.waiting_for_api_key)

@dp.message(TradingDataStates.waiting_for_api_key)
async def process_api_key(message: types.Message, state: FSMContext):
    api_key = message.text.strip()
    await state.update_data(api_key=api_key)
    await message.answer("أدخل السر السري API Secret:")
    await state.set_state(TradingDataStates.waiting_for_api_secret)

@dp.message(TradingDataStates.waiting_for_api_secret)
async def process_api_secret(message: types.Message, state: FSMContext):
    api_secret = message.text.strip()
    await state.update_data(api_secret=api_secret)
    await message.answer("إذا كانت المنصة تتطلب passphrase أدخله الآن، أو اكتب 'لا' لتخطي:")
    await state.set_state(TradingDataStates.waiting_for_passphrase)

@dp.message(TradingDataStates.waiting_for_passphrase)
async def process_passphrase(message: types.Message, state: FSMContext):
    passphrase = message.text.strip()
    if passphrase.lower() == 'لا':
        passphrase = None
    await state.update_data(passphrase=passphrase)

    data = await state.get_data()
    exchange = data.get("exchange")
    api_key = data.get("api_key")
    api_secret = data.get("api_secret")
    passphrase = data.get("passphrase")

    # تحقق من المفتاح
    await message.answer("جارٍ التحقق من صحة بيانات API... يرجى الانتظار.")
    valid, result_msg = await verify_api_key(exchange, api_key, api_secret, passphrase)

    if not valid:
        await message.answer(f"فشل التحقق: {result_msg}\nيرجى المحاولة مرة أخرى.")
        await state.clear()
        return

    # حفظ البيانات في قاعدة البيانات
    with SessionLocal() as session:
        # جلب أو إنشاء المستخدم
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            user = User(telegram_id=message.from_user.id)
            session.add(user)
            session.commit()
            session.refresh(user)

        # تحقق إذا المنصة موجودة للمستخدم
        api_key_obj = session.query(APIKey).filter_by(user_id=user.id, exchange=exchange).first()
        encrypted_key = encrypt_text(api_key)
        encrypted_secret = encrypt_text(api_secret)
        encrypted_passphrase = encrypt_text(passphrase) if passphrase else None

        if api_key_obj:
            # تحديث
            api_key_obj.api_key_encrypted = encrypted_key
            api_key_obj.api_secret_encrypted = encrypted_secret
            api_key_obj.passphrase_encrypted = encrypted_passphrase
            api_key_obj.is_active = True
        else:
            # إنشاء جديد
            new_api_key = APIKey(
                user_id=user.id,
                exchange=exchange,
                api_key_encrypted=encrypted_key,
                api_secret_encrypted=encrypted_secret,
                passphrase_encrypted=encrypted_passphrase,
                is_active=True
            )
            session.add(new_api_key)
        session.commit()

    await message.answer(f"تم تسجيل وتفعيل منصة {exchange} بنجاح ✅")
    await state.clear()

# ---- ابدأ استثمار ----
@dp.message(Text("ابدأ استثمار"))
async def start_investment(message: types.Message):
    await message.answer("بدء عملية الاستثمار بناءً على البيانات المسجلة... (سيتم تطويرها لاحقاً)")

# ---- استثمار وهمي ----
@dp.message(Text("استثمار وهمي"))
async def fake_investment(message: types.Message):
    await message.answer("عرض استثمار وهمي بدون أموال حقيقية... (سيتم تطويرها لاحقاً)")

# ---- كشف حساب عن فترة ----
@dp.message(Text("كشف حساب عن فترة"))
async def account_statement_request(message: types.Message, state: FSMContext):
    await message.answer("يرجى إدخال تاريخ بداية الفترة بصيغة YYYY-MM-DD:")
    await state.set_state("waiting_for_start_date")

@dp.message(state="waiting_for_start_date")
async def process_start_date(message: types.Message, state: FSMContext):
    start_date_str = message.text.strip()
    try:
        import datetime
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
    except Exception:
        await message.answer("التاريخ غير صالح، يرجى إدخال التاريخ بصيغة YYYY-MM-DD.")
        return
    await state.update_data(start_date=start_date)
    await message.answer("يرجى إدخال تاريخ نهاية الفترة بصيغة YYYY-MM-DD:")
    await state.set_state("waiting_for_end_date")

@dp.message(state="waiting_for_end_date")
async def process_end_date(message: types.Message, state: FSMContext):
    end_date_str = message.text.strip()
    try:
        import datetime
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
    except Exception:
        await message.answer("التاريخ غير صالح، يرجى إدخال التاريخ بصيغة YYYY-MM-DD.")
        return
    data = await state.get_data()
    start_date = data.get("start_date")

    # جلب بيانات التداول من قاعدة البيانات حسب التواريخ
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("لم يتم العثور على