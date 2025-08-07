from aiogram import Router, types
from aiogram.types import CallbackQuery
from database.crud import get_global_statistics

router = Router()

@router.callback_query(lambda c: c.data == "admin_stats")
async def show_stats(callback: CallbackQuery):
    stats = await get_global_statistics()
    msg = (
        f"📊 الإحصائيات العامة:\n\n"
        f"👥 العملاء: {stats['users']}\n"
        f"💰 إجمالي الإيداعات: {stats['deposits']} USDT\n"
        f"📈 الأرباح المحققة: {stats['profits']} USDT\n"
        f"🪙 عمولة البوت: {stats['bot_commission']} USDT"
    )
    await callback.message.edit_text(msg)
