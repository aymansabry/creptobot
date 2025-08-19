from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import Dispatcher
from services.exchange import verify_exchange_connection
from services.wallet import check_wallet_balance
from services.arbitrage import start_arbitrage, stop_arbitrage
from services.simulation import start_simulation
from services.report import get_user_report
from services.market import analyze_market
from utils.ui import colorize_button

dp = Dispatcher()

# قائمة تسجيل بيانات التداول
@dp.message_handler(lambda msg: msg.text == "📌 تسجيل بيانات التداول")
async def register_exchange(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🔷 اختر المنصة", callback_data="select_exchange"),
        InlineKeyboardButton("🔑 أدخل API Key", callback_data="enter_api"),
        InlineKeyboardButton("🔒 أدخل Secret Key", callback_data="enter_secret"),
        InlineKeyboardButton("🧪 أدخل Passphrase (اختياري)", callback_data="enter_passphrase"),
        InlineKeyboardButton("✅ تحقق من الاتصال", callback_data="verify_exchange"),
        InlineKeyboardButton("➕ إضافة منصة جديدة", callback_data="add_exchange"),
        InlineKeyboardButton("🛑 إيقاف منصة", callback_data="disable_exchange")
    )
    await msg.answer("اختر الإجراء المطلوب:", reply_markup=kb)

# قائمة المحفظة
@dp.message_handler(lambda msg: msg.text == "💼 محفظة المستخدم")
async def wallet_menu(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🔍 فحص الرصيد", callback_data="check_wallet"),
        InlineKeyboardButton("➕ إضافة محفظة جديدة", callback_data="add_wallet"),
        InlineKeyboardButton("🛑 إيقاف محفظة", callback_data="disable_wallet")
    )
    await msg.answer("إدارة المحفظة:", reply_markup=kb)

# قائمة مبلغ الاستثمار
@dp.message_handler(lambda msg: msg.text == "💰 مبلغ الاستثمار")
async def investment_amount_menu(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("💵 أدخل مبلغ الاستثمار", callback_data="enter_amount"),
        InlineKeyboardButton("✅ تأكيد الاستثمار", callback_data="confirm_investment"),
        InlineKeyboardButton("❌ إلغاء العملية", callback_data="cancel_investment")
    )
    await msg.answer("حدد مبلغ الاستثمار:", reply_markup=kb)

# قائمة بدء الاستثمار
@dp.message_handler(lambda msg: msg.text == "🚀 ابدأ استثمار")
async def start_investment_menu(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🚀 تشغيل الاستثمار الحقيقي", callback_data="start_real"),
        InlineKeyboardButton("📊 عرض حالة الاستثمار", callback_data="show_status"),
        InlineKeyboardButton("🛑 إيقاف الاستثمار", callback_data="stop_real")
    )
    await msg.answer("إدارة الاستثمار:", reply_markup=kb)

# قائمة الاستثمار الوهمي
@dp.message_handler(lambda msg: msg.text == "🎭 استثمار وهمي")
async def simulation_menu(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🎭 تفعيل المحاكاة", callback_data="start_simulation"),
        InlineKeyboardButton("📈 عرض النتائج", callback_data="show_simulation")
    )
    await msg.answer("وضع المحاكاة:", reply_markup=kb)

# قائمة كشف الحساب
@dp.message_handler(lambda msg: msg.text == "📊 كشف حساب عن فترة")
async def report_menu(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📅 اختر تاريخ البداية", callback_data="select_start"),
        InlineKeyboardButton("📅 اختر تاريخ النهاية", callback_data="select_end"),
        InlineKeyboardButton("📊 عرض التقرير", callback_data="show_report")
    )
    await msg.answer("كشف الحساب:", reply_markup=kb)

# قائمة حالة السوق
@dp.message_handler(lambda msg: msg.text == "📉 حالة السوق")
async def market_menu(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📉 تحليل السوق", callback_data="analyze_market"),
        InlineKeyboardButton("💡 نصائح الاستثمار", callback_data="market_tips")
    )
    await msg.answer("تحليل السوق:", reply_markup=kb)

# قائمة إيقاف الاستثمار
@dp.message_handler(lambda msg: msg.text == "🛑 إيقاف الاستثمار")
async def stop_investment_menu(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🛑 إيقاف كامل", callback_data="stop_all"),
        InlineKeyboardButton("🔄 إعادة التفعيل لاحقًا", callback_data="reactivate")
    )
    await msg.answer("إيقاف الاستثمار:", reply_markup=kb)