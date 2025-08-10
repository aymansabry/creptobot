import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text, StateFilter
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import and_
from cryptography.fernet import Fernet, InvalidToken
import datetime
import ccxt.async_support as ccxt_async

from database import create_tables, SessionLocal
from models import User, APIKey, TradeLog
from settings import BOT_TOKEN, OWNER_ID, FERNET_KEY

create_tables()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

fernet = Fernet(FERNET_KEY.encode())

class InvestmentStates(StatesGroup):
    waiting_for_exchange_name = State()
    waiting_for_api_key = State()
    waiting_for_api_secret = State()
    waiting_for_passphrase = State()
    waiting_for_investment_amount = State()
    waiting_for_report_start_date = State()
    waiting_for_report_end_date = State()

# هنا اللوحات المصححة - InlineKeyboardMarkup تحتاج inline_keyboard مع صفوف من الأزرار

user_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="مساعدة /help", callback_data="help"),
            InlineKeyboardButton(text="تسجيل/تعديل بيانات التداول", callback_data="register_trading_data"),
        ],
        [
            InlineKeyboardButton(text="ابدأ استثمار", callback_data="start_investment"),
            InlineKeyboardButton(text="استثمار وهمي", callback_data="fake_investment"),
        ],
        [
            InlineKeyboardButton(text="كشف حساب عن فترة", callback_data="account_statement"),
            InlineKeyboardButton(text="حالة السوق", callback_data="market_status"),
        ],
        [
            InlineKeyboardButton(text="ايقاف الاستثمار", callback_data="stop_investment"),
        ]
    ]
)

owner_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="/help", callback_data="help"),
            InlineKeyboardButton(text="/admin_panel", callback_data="admin_panel"),
        ],
        [
            InlineKeyboardButton(text="تعديل نسبة ربح البوت", callback_data="edit_profit_percentage"),
            InlineKeyboardButton(text="عدد المستخدمين", callback_data="user_count"),
        ],
        [
            InlineKeyboardButton(text="عدد المستخدمين أونلاين", callback_data="online_user_count"),
            InlineKeyboardButton(text="تقارير الاستثمار", callback_data="investment_reports"),
        ],
        [
            InlineKeyboardButton(text="حالة البوت البرمجية", callback_data="bot_status"),
        ]
    ]
)

def safe_encrypt(text):
    return fernet.encrypt(text.encode()).decode()

def safe_decrypt(token):
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        return None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.answer("أهلاً مالك البوت!", reply_markup=owner_inline_keyboard)
    else:
        with SessionLocal() as session:
            user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
            if not user:
                user = User(telegram_id=message.from_user.id)
                session.add(user)
                session.commit()
        await message.answer("أهلاً! البوت يعمل بنجاح.", reply_markup=user_inline_keyboard)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.reply(
        "أوامر البوت:\n"
        "/start\n"
        "/help\n"
        "تسجيل/تعديل بيانات التداول\n"
        "ابدأ استثمار\n"
        "استثمار وهمي\n"
        "كشف حساب عن فترة\n"
        "حالة السوق\n"
        "ايقاف الاستثمار\n"
    )

# باقي الدوال كما هي (start_api_key_registration، receive_api_key، receive_api_secret، receive_passphrase، skip_passphrase، save_api_keys، start_investment، process_investment_amount، run_investment_for_user، fake_investment، ask_report_start_date، handle_date_selection، generate_report، market_status_report، stop_investment، cmd_admin_panel)

@dp.callback_query(lambda c: True)
async def handle_callbacks(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    user_id = callback_query.from_user.id
    message = callback_query.message

    if data == "help":
        await cmd_help(message)
    elif data == "register_trading_data":
        await start_api_key_registration(message, state)
    elif data.startswith("select_exchange_"):
        exchange = data.replace("select_exchange_", "")
        await state.update_data(exchange=exchange)
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(user_id, f"أدخل مفتاح API لمنصة {exchange.capitalize()}:")
        await state.set_state(InvestmentStates.waiting_for_api_key)
    elif data == "start_investment":
        await start_investment(message, state)
    elif data == "fake_investment":
        await fake_investment(message)
    elif data == "account_statement":
        await ask_report_start_date(message, state)
    elif data == "market_status":
        await market_status_report(message)
    elif data == "stop_investment":
        await stop_investment(message)
    elif data == "admin_panel":
        if user_id != int(OWNER_ID):
            await bot.answer_callback_query(callback_query.id, text="غير مصرح لك باستخدام هذه الأوامر.", show_alert=True)
            return
        await cmd_admin_panel(message)
    elif data == "edit_profit_percentage":
        await bot.answer_callback_query(callback_query.id, text="ميزة تعديل نسبة الربح تحت التطوير.", show_alert=True)
    elif data == "user_count":
        with SessionLocal() as session:
            count = session.query(User).count()
        await bot.send_message(user_id, f"عدد المستخدمين: {count}")
    elif data == "online_user_count":
        await bot.send_message(user_id, "ميزة عدد المستخدمين أونلاين تحت التطوير.")
    elif data == "investment_reports":
        await bot.send_message(user_id, "ميزة تقارير الاستثمار تحت التطوير.")
    elif data == "bot_status":
        await bot.send_message(user_id, "حالة البوت: يعمل بشكل طبيعي ✅")
    elif data.startswith("date_"):
        await handle_date_selection(callback_query, state)
    else:
        await bot.answer_callback_query(callback_query.id, text="خيار غير معروف", show_alert=True)
        return

    await bot.answer_callback_query(callback_query.id)

async def main():
    print("البوت بدأ العمل")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())