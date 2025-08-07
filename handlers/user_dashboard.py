from aiogram import Router, types
from utils.buttons import user_menu
from database.crud import get_user_investments

router = Router()

@router.message(lambda msg: msg.text == "📊 حسابي")
async def dashboard(msg: types.Message):
    data = await get_user_investments(msg.from_user.id)
    text = (
        f"🧾 استثماراتك:\n\n"
        f"✅ الصفقات الناجحة: {data['successful']}\n"
        f"💸 الأرباح الكلية: {data['profit']} USDT\n"
        f"⏳ صفقات قيد التنفيذ: {data['active']}\n"
    )
    await msg.answer(text, reply_markup=user_menu())
