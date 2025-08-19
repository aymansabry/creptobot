from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import Dispatcher
from services.admin import (
    update_profit_margin,
    get_total_users,
    get_online_users,
    get_global_report,
    check_bot_health,
    simulate_user_session
)

dp = Dispatcher()

# قائمة المدير الرئيسية
@dp.message_handler(lambda msg: msg.text == "🛠️ مدير النظام")
async def admin_main_menu(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("⚙️ تعديل نسبة الربح", callback_data="edit_profit"),
        InlineKeyboardButton("👥 عدد المستخدمين الإجمالي", callback_data="total_users"),
        InlineKeyboardButton("🟢 عدد المستخدمين النشطين", callback_data="online_users"),
        InlineKeyboardButton("📊 تقارير الاستثمار عن فترة", callback_data="global_report"),
        InlineKeyboardButton("🧠 حالة البوت برمجيا", callback_data="bot_health"),
        InlineKeyboardButton("👤 التداول كمستخدم عادي", callback_data="simulate_user")
    )
    await msg.answer("لوحة تحكم المدير:", reply_markup=kb)

# تعديل نسبة الربح
@dp.callback_query_handler(lambda c: c.data == "edit_profit")
async def edit_profit_callback(call: types.CallbackQuery):
    await call.message.answer("أدخل النسبة الجديدة للربح (مثال: 0.05):")

# عدد المستخدمين الإجمالي
@dp.callback_query_handler(lambda c: c.data == "total_users")
async def total_users_callback(call: types.CallbackQuery):
    count = await get_total_users()
    await call.message.answer(f"📌 عدد المستخدمين الإجمالي: {count}")

# عدد المستخدمين النشطين
@dp.callback_query_handler(lambda c: c.data == "online_users")
async def online_users_callback(call: types.CallbackQuery):
    count = await get_online_users()
    await call.message.answer(f"🟢 عدد المستخدمين النشطين الآن: {count}")

# تقارير الاستثمار عن فترة
@dp.callback_query_handler(lambda c: c.data == "global_report")
async def global_report_callback(call: types.CallbackQuery):
    await call.message.answer("📅 أدخل تاريخ البداية والنهاية للحصول على التقرير الإجمالي:")

# حالة البوت برمجيا
@dp.callback_query_handler(lambda c: c.data == "bot_health")
async def bot_health_callback(call: types.CallbackQuery):
    status = await check_bot_health()
    await call.message.answer(f"🧠 حالة البوت:\n{status}")

# التداول كمستخدم عادي
@dp.callback_query_handler(lambda c: c.data == "simulate_user")
async def simulate_user_callback(call: types.CallbackQuery):
    await simulate_user_session(call.from_user.id)
    await call.message.answer("✅ تم تفعيل وضع المستخدم العادي لتجربة البوت.")