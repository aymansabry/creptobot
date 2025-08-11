from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os
import openai  # لاحقاً لو معاك مفتاح OpenAI في env

router = Router()

admin_ids_str = os.getenv("TELEGRAM_ADMIN_IDS", "")
ADMIN_IDS = set()
if admin_ids_str:
    ADMIN_IDS = set(int(i) for i in admin_ids_str.split(",") if i.strip().isdigit())

# تعريف الحالات (States) للفيم مع حالة محفظة العميل
class UserStates(StatesGroup):
    choosing_mode = State()
    entering_binance_api = State()
    entering_binance_secret = State()
    entering_kucoin_api = State()
    entering_kucoin_secret = State()
    entering_kucoin_passphrase = State()
    entering_investment_amount = State()
    entering_wallet_address = State()  # جديدة

def mode_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="فعلي 💰", callback_data="mode_live"),
            InlineKeyboardButton(text="وهمي 🧪", callback_data="mode_demo"),
        ]
    ])
    return keyboard

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "مرحبًا بك في بوت المراجحة التلقائية!\n"
        "اختر الوضع الذي تريد العمل به:",
        reply_markup=mode_keyboard()
    )
    await state.set_state(UserStates.choosing_mode)

@router.callback_query(F.data.startswith("mode_"))
async def process_mode_selection(callback: CallbackQuery, state: FSMContext):
    mode = callback.data.split("_")[1]  # live أو demo
    await state.update_data(mode=mode)
    explanation = ""
    if mode == "live":
        explanation = "لقد اخترت الوضع الفعلي. سيتم تنفيذ الصفقات الحقيقية باستخدام أموالك."
    else:
        explanation = "لقد اخترت الوضع الوهمي. لن تتم أي صفقات حقيقية، وستتلقى بيانات محاكاة فقط."

    await callback.message.answer(f"{explanation}\n\nالآن أدخل مفتاح API الخاص بمنصة Binance:")
    await state.set_state(UserStates.entering_binance_api)
    await callback.answer()

@router.message(UserStates.entering_binance_api)
async def process_binance_api(message: Message, state: FSMContext):
    api_key = message.text.strip()
    await state.update_data(binance_api_key=api_key)
    await message.answer("حسنًا، الآن أدخل السر الخاص بـ Binance:")
    await state.set_state(UserStates.entering_binance_secret)

@router.message(UserStates.entering_binance_secret)
async def process_binance_secret(message: Message, state: FSMContext):
    secret_key = message.text.strip()
    await state.update_data(binance_secret_key=secret_key)
    await message.answer("الآن أدخل مفتاح API الخاص بمنصة KuCoin:")
    await state.set_state(UserStates.entering_kucoin_api)

@router.message(UserStates.entering_kucoin_api)
async def process_kucoin_api(message: Message, state: FSMContext):
    api_key = message.text.strip()
    await state.update_data(kucoin_api_key=api_key)
    await message.answer("الآن أدخل السر الخاص بـ KuCoin:")
    await state.set_state(UserStates.entering_kucoin_secret)

@router.message(UserStates.entering_kucoin_secret)
async def process_kucoin_secret(message: Message, state: FSMContext):
    secret_key = message.text.strip()
    await state.update_data(kucoin_secret_key=secret_key)
    await message.answer("وأخيرًا، أدخل كلمة المرور (Passphrase) الخاصة بـ KuCoin:")
    await state.set_state(UserStates.entering_kucoin_passphrase)

@router.message(UserStates.entering_kucoin_passphrase)
async def process_kucoin_passphrase(message: Message, state: FSMContext):
    passphrase = message.text.strip()
    await state.update_data(kucoin_passphrase=passphrase)
    await message.answer("الآن أدخل مبلغ الاستثمار (بالدولار):")
    await state.set_state(UserStates.entering_investment_amount)

@router.message(UserStates.entering_investment_amount)
async def process_investment_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("الرجاء إدخال مبلغ صالح (رقم أكبر من صفر).")
        return
    await state.update_data(investment_amount=amount)
    await message.answer("الرجاء إدخال عنوان محفظتك (Wallet Address):")
    await state.set_state(UserStates.entering_wallet_address)

@router.message(UserStates.entering_wallet_address)
async def process_wallet_address(message: Message, state: FSMContext):
    wallet = message.text.strip()
    await state.update_data(wallet_address=wallet)

    data = await state.get_data()
    mode = data.get("mode", "demo")

    from security import encrypt_api_key
    from db import save_user_data

    encrypted_data = {
        "binance_api_key": encrypt_api_key(data["binance_api_key"]),
        "binance_secret_key": encrypt_api_key(data["binance_secret_key"]),
        "kucoin_api_key": encrypt_api_key(data["kucoin_api_key"]),
        "kucoin_secret_key": encrypt_api_key(data["kucoin_secret_key"]),
        "kucoin_passphrase": encrypt_api_key(data["kucoin_passphrase"]),
        "investment_amount": data["investment_amount"],
        "wallet_address": wallet,
        "mode": mode,
    }

    await save_user_data(message.from_user.id, encrypted_data)

    await message.answer(
        f"تم حفظ بياناتك بنجاح!\n"
        f"الوضع: {'فعلي' if mode=='live' else 'وهمي'}\n"
        f"مبلغ الاستثمار: {data['investment_amount']} دولار\n"
        f"محفظتك: {wallet}\n\n"
        "سيبدأ البوت العمل تلقائيًا وسيتم إعلامك بالأرباح."
    )
    await state.clear()

# أمر خاص للمدير لعرض المستخدمين
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("🚫 أنت لست مديرًا لهذا البوت.")
        return
    from db import fetch_all_users
    users = await fetch_all_users()
    text = "قائمة المستخدمين:\n"
    for u in users:
        text += f"- {u['telegram_id']} | رصيد: {u.get('total_profit_loss', 0):.4f}\n"
    await message.answer(text or "لا يوجد مستخدمين بعد.")

# أمر تحليل السوق باستخدام OpenAI
@router.message(Command("market_analysis"))
async def market_analysis(message: Message):
    await message.answer("جاري تحليل السوق، يرجى الانتظار...")
    openai.api_key = os.getenv("OPENAI_API_KEY")
    prompt = (
        "قدم لي تحليل موجز للسوق الحالي لعملة البيتكوين والتوقعات المستقبلية."
    )
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        result = response.choices[0].message.content
        await message.answer(result)
    except Exception as e:
        await message.answer(f"حدث خطأ أثناء تحليل السوق: {e}")

# أمر نصائح التداول باستخدام OpenAI
@router.message(Command("trade_tips"))
async def trade_tips(message: Message):
    await message.answer("جاري جلب نصائح التداول، يرجى الانتظار...")
    openai.api_key = os.getenv("OPENAI_API_KEY")
    prompt = (
        "قدم لي نصائح تداول ذكية للمراجحة بين منصتي Binance و KuCoin."
    )
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
        )
        result = response.choices[0].message.content
        await message.answer(result)
    except Exception as e:
        await message.answer(f"حدث خطأ أثناء جلب النصائح: {e}")
