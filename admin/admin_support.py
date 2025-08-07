from aiogram import Router, types
from aiogram.types import CallbackQuery
from database.crud import get_support_tickets

router = Router()

@router.callback_query(lambda c: c.data == "admin_support")
async def view_tickets(callback: CallbackQuery):
    tickets = await get_support_tickets()
    if not tickets:
        await callback.message.edit_text("✅ لا توجد رسائل دعم حاليًا.")
        return
    msg = "🧾 رسائل الدعم:\n\n"
    for t in tickets:
        msg += f"— من {t['user_id']}:\n{t['message']}\n\n"
    await callback.message.edit_text(msg)
