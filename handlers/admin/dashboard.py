from aiogram import Dispatcher, types
from db.crud import get_system_stats
from db.session import get_db

async def show_admin_dashboard(message: types.Message):
    """عرض لوحة التحكم الإدارية"""
    db = next(get_db())
    try:
        stats = get_system_stats(db)
        await message.answer(
            "📊 <b>لوحة التحكم الإدارية</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"• عدد المستخدمين: {stats['total_users']}\n"
            f"• الصفقات النشطة: {stats['active_trades']}\n"
            f"• إجمالي الأرباح: {stats['total_profits']} USDT",
            parse_mode="HTML"
        )
    finally:
        db.close()

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(
        show_admin_dashboard,
        commands=["dashboard"],
        state="*"
    )
