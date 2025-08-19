from aiogram import types
from aiogram.dispatcher import Dispatcher
from handlers.user_menu import (
    register_exchange,
    wallet_menu,
    investment_amount_menu,
    start_investment_menu,
    simulation_menu,
    report_menu,
    market_menu,
    stop_investment_menu
)

dp = Dispatcher()

# واجهة البداية
@dp.message_handler(commands=["start"])
async def start_bot(msg: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        "📌 تسجيل بيانات التداول",
        "💼 محفظة المستخدم",
        "💰 مبلغ الاستثمار"
    )
    kb.add(
        "🚀 ابدأ استثمار",
        "🎭 استثمار وهمي",
        "📊 كشف حساب عن فترة"
    )
    kb.add(
        "📉 حالة السوق",
        "🛑 إيقاف الاستثمار"
    )
    await msg.answer("مرحبًا بك يا زيوس 👋\nاختر من القوائم التالية:", reply_markup=kb)

# ربط كل زر بالقائمة التفاعلية الخاصة به
@dp.message_handler(lambda msg: msg.text == "📌 تسجيل بيانات التداول")
async def open_exchange_menu(msg: types.Message):
    await register_exchange(msg)

@dp.message_handler(lambda msg: msg.text == "💼 محفظة المستخدم")
async def open_wallet_menu(msg: types.Message):
    await wallet_menu(msg)

@dp.message_handler(lambda msg: msg.text == "💰 مبلغ الاستثمار")
async def open_investment_menu(msg: types.Message):
    await investment_amount_menu(msg)

@dp.message_handler(lambda msg: msg.text == "🚀 ابدأ استثمار")
async def open_start_menu(msg: types.Message):
    await start_investment_menu(msg)

@dp.message_handler(lambda msg: msg.text == "🎭 استثمار وهمي")
async def open_simulation_menu(msg: types.Message):
    await simulation_menu(msg)

@dp.message_handler(lambda msg: msg.text == "📊 كشف حساب عن فترة")
async def open_report_menu(msg: types.Message):
    await report_menu(msg)

@dp.message_handler(lambda msg: msg.text == "📉 حالة السوق")
async def open_market_menu(msg: types.Message):
    await market_menu(msg)

@dp.message_handler(lambda msg: msg.text == "🛑 إيقاف الاستثمار")
async def open_stop_menu(msg: types.Message):
    await stop_investment_menu(msg)