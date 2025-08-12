import asyncio
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from openai import OpenAI
import logging

# إعدادات
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
DATABASE_URL = "mysql+pymysql://user:password@host/dbname"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# موديل المستخدم
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    binance_api = Column(String(256), nullable=True)
    binance_secret = Column(String(256), nullable=True)
    kucoin_api = Column(String(256), nullable=True)
    kucoin_secret = Column(String(256), nullable=True)
    kucoin_passphrase = Column(String(256), nullable=True)
    investment_amount = Column(Float, default=0.0)
    investment_status = Column(String(20), default="stopped")  # started, stopped, waiting_approval

Base.metadata.create_all(engine)

openai = OpenAI(api_key=OPENAI_API_KEY)

# FSM للحالات المختلفة
class Form(StatesGroup):
    waiting_binance_api = State()
    waiting_binance_secret = State()
    waiting_kucoin_api = State()
    waiting_kucoin_secret = State()
    waiting_kucoin_passphrase = State()
    waiting_investment_amount = State()
    waiting_approval = State()

# --- أوامر البداية ---
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(
        "مرحباً بك في بوت الاستثمار الآلي!\n"
        "يمكنك ربط حساباتك وتحديد مبلغ الاستثمار.\n\n"
        "الأوامر المتاحة:\n"
        "/link_binance - ربط حساب Binance\n"
        "/link_kucoin - ربط حساب KuCoin\n"
        "/set_investment - تحديد مبلغ الاستثمار\n"
        "/start_invest - بدء الاستثمار\n"
        "/stop_invest - إيقاف الاستثمار"
    )

# --- ربط حساب Binance ---
@dp.message_handler(commands=['link_binance'])
async def link_binance_start(message: types.Message):
    await message.answer("أرسل مفتاح API الخاص بـ Binance:")
    await Form.waiting_binance_api.set()

@dp.message_handler(state=Form.waiting_binance_api)
async def process_binance_api(message: types.Message, state: FSMContext):
    api_key = message.text.strip()
    # تحقق مبدئي (مثلاً الطول)
    if len(api_key) < 20:
        await message.reply("المفتاح غير صالح، حاول مرة أخرى.")
        return
    await state.update_data(binance_api=api_key)
    await message.answer("أرسل السر الخاص بـ Binance:")
    await Form.waiting_binance_secret.set()

@dp.message_handler(state=Form.waiting_binance_secret)
async def process_binance_secret(message: types.Message, state: FSMContext):
    secret = message.text.strip()
    if len(secret) < 20:
        await message.reply("السر غير صالح، حاول مرة أخرى.")
        return
    data = await state.get_data()
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id)
        db.add(user)
    user.binance_api = data['binance_api']
    user.binance_secret = secret
    db.commit()
    db.close()
    await message.answer("تم ربط حساب Binance بنجاح ✅")
    await state.finish()

# --- ربط حساب KuCoin ---
@dp.message_handler(commands=['link_kucoin'])
async def link_kucoin_start(message: types.Message):
    await message.answer("أرسل مفتاح API الخاص بـ KuCoin:")
    await Form.waiting_kucoin_api.set()

@dp.message_handler(state=Form.waiting_kucoin_api)
async def process_kucoin_api(message: types.Message, state: FSMContext):
    api_key = message.text.strip()
    if len(api_key) < 20:
        await message.reply("المفتاح غير صالح، حاول مرة أخرى.")
        return
    await state.update_data(kucoin_api=api_key)
    await message.answer("أرسل السر الخاص بـ KuCoin:")
    await Form.waiting_kucoin_secret.set()

@dp.message_handler(state=Form.waiting_kucoin_secret)
async def process_kucoin_secret(message: types.Message, state: FSMContext):
    secret = message.text.strip()
    if len(secret) < 20:
        await message.reply("السر غير صالح، حاول مرة أخرى.")
        return
    await state.update_data(kucoin_secret=secret)
    await message.answer("أرسل عبارة المرور الخاصة بـ KuCoin:")
    await Form.waiting_kucoin_passphrase.set()

@dp.message_handler(state=Form.waiting_kucoin_passphrase)
async def process_kucoin_passphrase(message: types.Message, state: FSMContext):
    passphrase = message.text.strip()
    data = await state.get_data()
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id)
        db.add(user)
    user.kucoin_api = data['kucoin_api']
    user.kucoin_secret = data['kucoin_secret']
    user.kucoin_passphrase = passphrase
    db.commit()
    db.close()
    await message.answer("تم ربط حساب KuCoin بنجاح ✅")
    await state.finish()

# --- تحديد مبلغ الاستثمار ---
@dp.message_handler(commands=['set_investment'])
async def set_investment_start(message: types.Message):
    await message.answer("أرسل مبلغ الاستثمار بالدولار (مثال: 1000):")
    await Form.waiting_investment_amount.set()

@dp.message_handler(state=Form.waiting_investment_amount)
async def process_investment_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.reply("الرجاء إدخال مبلغ صحيح أكبر من 0.")
        return

    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id)
        db.add(user)
    user.investment_amount = amount
    db.commit()
    db.close()
    await message.answer(f"تم تعيين مبلغ الاستثمار إلى {amount} دولار ✅")
    await state.finish()

# --- بدء الاستثمار مع طلب موافقة في حال الرصيد أقل ---
@dp.message_handler(commands=['start_invest'])
async def start_invest(message: types.Message, state: FSMContext):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if not user:
        await message.reply("يجب ربط حساب التداول أولاً.")
        db.close()
        return
    if user.investment_status == "started":
        await message.reply("الاستثمار جاري بالفعل.")
        db.close()
        return
    if user.investment_amount <= 0:
        await message.reply("حدد مبلغ الاستثمار أولاً باستخدام /set_investment.")
        db.close()
        return

    # هنا مثال: تحقق من الرصيد الفعلي (استبدل بجلب الرصيد الحقيقي عبر API)
    user_balance = user.investment_amount * 0.8  # لنفترض الرصيد أقل (80%) للمثال

    if user_balance < user.investment_amount:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("استخدام الرصيد المتاح بالكامل", callback_data="use_full_balance"))
        keyboard.add(types.InlineKeyboardButton("إلغاء", callback_data="cancel_invest"))
        await message.answer(
            f"رصيدك الحالي ({user_balance}$) أقل من مبلغ الاستثمار المحدد ({user.investment_amount}$).\n"
            "هل تريد المتابعة باستخدام الرصيد المتاح بالكامل؟",
            reply_markup=keyboard
        )
        await Form.waiting_approval.set()
        db.close()
        return

    # إذا الرصيد كافي، يبدأ الاستثمار مباشرة
    user.investment_status = "started"
    db.commit()
    db.close()
    await message.reply("تم بدء الاستثمار. سيتم إشعارك بكل عملية.")
    asyncio.create_task(investment_loop(user.telegram_id))

@dp.callback_query_handler(lambda c: c.data in ['use_full_balance', 'cancel_invest'], state=Form.waiting_approval)
async def approval_callback(call: types.CallbackQuery, state: FSMContext):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == call.from_user.id).first()
    if not user:
        await call.answer("حدث خطأ، حاول لاحقاً.", show_alert=True)
        await state.finish()
        db.close()
        return

    if call.data == "use_full_balance":
        user.investment_amount *= 0.8  # استخدام الرصيد المتاح (مثال)
        user.investment_status = "started"
        db.commit()
        db.close()
        await call.message.edit_text("تم تعديل مبلغ الاستثمار ليتناسب مع رصيدك وبدء الاستثمار.")
        await state.finish()
        asyncio.create_task(investment_loop(user.telegram_id))
    else:
        user.investment_status = "stopped"
        db.commit()
        db.close()
        await call.message.edit_text("تم إلغاء بدء الاستثمار.")
        await state.finish()

# --- إيقاف الاستثمار ---
@dp.message_handler(commands=['stop_invest'])
async def stop_invest(message: types.Message):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if user and user.investment_status == "started":
        user.investment_status = "stopped"
        db.commit()
        db.close()
        await message.reply("تم إيقاف الاستثمار.")
    else:
        db.close()
        await message.reply("لا يوجد استثمار جاري.")

# --- الحلقة الرئيسية للاستثمار (مبسطة) ---
async def investment_loop(telegram_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        db.close()
        return

    while user.investment_status == "started":
        try:
            # جلب الأسعار (استبدل بجلب حقيقي من API)
            binance_price, kucoin_price = 10000.0, 10020.0
            # حساب فرصة المراجحة
            diff = kucoin_price - binance_price
            fee = (binance_price + kucoin_price) * 0.001
            profit = diff - fee
            has_opportunity = profit > 0

            if has_opportunity:
                # استشارة OpenAI
                prompt = (
                    f"Given prices Binance: {binance_price}, KuCoin: {kucoin_price}, "
                    f"profit after fees: {profit:.2f}. Should we proceed with arbitrage? Answer YES or NO."
                )
                response = await openai.chat.completions.acreate(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                decision = response.choices[0].message.content.strip().upper().startswith("YES")
                if decision:
                    # تنفيذ الصفقة (مبسطة - أضف التنفيذ الحقيقي هنا)
                    user.investment_amount += profit  # تحديث رصيد
                    db.commit()
                    await bot.send_message(telegram_id, f"تم تنفيذ مراجحة مربحة بقيمة {profit:.2f} دولار.")
                else:
                    await bot.send_message(telegram_id, "فرصة المراجحة غير مناسبة حالياً.")
            else:
                await bot.send_message(telegram_id, "لا توجد فرص مراجحة الآن.")

            db.refresh(user)
            await asyncio.sleep(30)
        except Exception as e:
            logging.error(f"خطأ في حلقة الاستثمار للمستخدم {telegram_id}: {e}")
            await bot.send_message(telegram_id, f"حدث خطأ: {e}")
            await asyncio.sleep(60)

    db.close()
    await bot.send_message(telegram_id, "تم إيقاف الاستثمار بناءً على طلبك.")

# --- تشغيل البوت ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
