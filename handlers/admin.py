from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# لوحة التحكم الإدارية
@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if str(message.from_user.id) not in config.ADMINS:
        return await message.answer("❌ ليس لديك صلاحية الدخول هنا")
    
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="إحصائيات", callback_data="admin_stats"),
        types.InlineKeyboardButton(text="إدارة الصفقات", callback_data="admin_deals"),
        types.InlineKeyboardButton(text="إرسال إشعار", callback_data="admin_notify")
    )
    builder.adjust(1)
    
    await message.answer(
        "👨‍💻 لوحة التحكم الإدارية",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: types.CallbackQuery):
    # كود جلب الإحصائيات من قاعدة البيانات
    await callback.answer("📊 الإحصائيات:\n\n- عدد المستخدمين: 150\n- الصفقات النشطة: 12")
