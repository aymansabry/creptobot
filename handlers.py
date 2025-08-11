from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os

router = Router()

ADMIN_IDS = set(map(int, os.getenv("TELEGRAM_ADMIN_IDS", "").split(',')))

# تعريف الحالات (States) للفيم
class UserStates(StatesGroup):
    choosing_mode = State()
    entering_binance_api = State()
    entering_binance_secret = State()
    entering_kucoin_api = State()
    entering_kucoin_secret = State()
    entering_kucoin_passphrase = State()
    entering_investment_amount = State()

# لوحة الاختيار بين وهمي وفعلي
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

@router.callback_query(Text(startswith="mode_"))
async def process_mode_selection(callback: CallbackQuery, state: FSMContext):
    mode = callback.data.split("_")[1]  # live أو demo
    await state.update_data(mode=mode)
    await callback.message.answer(f"اخترنا الوضع: {mode}\n\nالآن أدخل مفتاح API الخاص بمنصة Binance:")
    await state.set_state(UserStates.entering_binance_api)
    await callback.answer()

@router.message(UserStates.entering_binance_api)
async def process_binance_api(message: Message, state: FSMContext):
    api_key = message.text.strip()
    # هنا ممكن تضيف تحقق بسيط من شكل المفتاح
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
    
    data = await state.get_data()
    mode = data.get("mode", "demo")
    
    # هنا تحفظ كل البيانات في قاعدة البيانات، مع تشفير المفاتيح
    # ممكن تضيف دالة خاصة تحفظ بيانات المستخدم، أنا أفترض دالة save_user_data(telegram_id, data)
    from security import encrypt_api_key
    from db import save_user_data

    encrypted_data = {
        "binance_api_key": encrypt_api_key(data["binance_api_key"]),
        "binance_secret_key": encrypt_api_key(data["binance_secret_key"]),
        "kucoin_api_key": encrypt_api_key(data["kucoin_api_key"]),
        "kucoin_secret_key": encrypt_api_key(data["kucoin_secret_key"]),
        "kucoin_passphrase": encrypt_api_key(data["kucoin_passphrase"]),
        "investment_amount": amount,
        "mode": mode,
    }

    await save_user_data(message.from_user.id, encrypted_data)

    await message.answer(
        f"تم حفظ بياناتك بنجاح!\n"
        f"الوضع: {'فعلي' if mode=='live' else 'وهمي'}\n"
        f"مبلغ الاستثمار: {amount} دولار\n\n"
        "سيبدأ البوت العمل تلقائيًا وسيتم إعلامك بالأرباح."
    )
    await state.clear()

# أمر خاص للمدير لعرض المستخدمين أو رصيدهم، مثال بسيط
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("🚫 أنت لست مديرًا لهذا البوت.")
        return
    # استعلام بسيط لجلب المستخدمين وأرباحهم
    from db import fetch_all_users
    users = await fetch_all_users()
    text = "قائمة المستخدمين:\n"
    for u in users:
        text += f"- {u['telegram_id']} | رصيد: {u.get('total_profit_loss',0):.4f}\n"
    await message.answer(text or "لا يوجد مستخدمين بعد.")

