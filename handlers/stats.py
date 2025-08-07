from aiogram import Router, types
from database.crud import get_deal_stats
from utils.permissions import is_admin

router = Router()

@router.message(lambda msg: msg.text == "📊 إحصائيات الصفقات")
async def show_stats(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ لا تملك صلاحية.")

    stats = await get_deal_stats()
    msg_text = (
        f"📊 إحصائيات عامة:\n\n"
        f"📈 الصفقات الناجحة: {stats['success']}\n"
        f"❌ الفاشلة: {stats['fail']}\n"
        f"💵 إجمالي الربح: {stats['total']} USDT"
    )
    await msg.answer(msg_text)
