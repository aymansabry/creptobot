from aiogram import Router, types
from aiogram.types import CallbackQuery
from database.crud import get_active_trades

router = Router()

@router.callback_query(lambda c: c.data == "admin_trades")
async def show_trades(callback: CallbackQuery):
    trades = await get_active_trades()
    if not trades:
        await callback.message.edit_text("💼 لا توجد صفقات جارية حاليًا.")
        return
    msg = "📋 الصفقات النشطة:\n\n"
    for t in trades:
        msg += f"— {t['user_id']} | {t['amount']} USDT | {t['profit']}% قيد التنفيذ\n"
    await callback.message.edit_text(msg)
