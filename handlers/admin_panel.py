from aiogram import Router, types
from utils.buttons import admin_menu
from database.crud import get_stats
from utils.permissions import is_admin

router = Router()

@router.message(lambda msg: msg.text == "📈 لوحة التحكم")
async def admin_panel(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ ليس لديك صلاحية الدخول.")
    
    stats = await get_stats()
    text = (
        f"👑 لوحة المدير:\n\n"
        f"👥 عدد المستخدمين: {stats['users']}\n"
        f"💼 استثمارات نشطة: {stats['active_investments']}\n"
        f"💰 إجمالي الأرباح: {stats['total_profit']} USDT\n"
    )
    await msg.answer(text, reply_markup=admin_menu())
