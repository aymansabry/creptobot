from aiogram import Dispatcher, types, F
from config import OWNER_TELEGRAM_ID
from src.services.admin import get_dashboard_data, set_bot_profit_percentage

async def admin_dashboard(msg: types.Message):
    if msg.from_user.id != OWNER_TELEGRAM_ID:
        return await msg.answer("🚫 غير مصرح لك.")
    stats = await get_dashboard_data()
    await msg.answer(f"📊 لوحة الإدارة:\n\n{stats}")

async def set_profit(msg: types.Message):
    if msg.from_user.id != OWNER_TELEGRAM_ID:
        return
    try:
        percentage = float(msg.text.split(" ")[1])
        await set_bot_profit_percentage(percentage)
        await msg.answer(f"تم تحديث نسبة ربح البوت إلى: {percentage}%")
    except:
        await msg.answer("❌ صيغة خاطئة. استخدم: /setprofit 3.5")

def register_admin_handlers(dp: Dispatcher):
    dp.message.register(admin_dashboard, F.text == "🛠 لوحة المدير")
    dp.message.register(set_profit, F.text.startswith("/setprofit"))
