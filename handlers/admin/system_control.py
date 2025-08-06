from aiogram import types
from aiogram.dispatcher import FSMContext
from db.crud import get_system_settings, update_system_settings
from db.session import get_db
from templates.menu_templates import admin_control_menu
from core.config import SystemConfig

async def show_control_panel(message: types.Message):
    """عرض لوحة تحكم المدير"""
    db = next(get_db())
    try:
        settings = get_system_settings(db)
        menu = admin_control_menu(settings)
        await message.answer(
            "⚙️ <b>لوحة تحكم النظام</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"• الوضع الحقيقي: {'✅ مفعل' if settings.real_trading_enabled else '❌ معطل'}\n"
            f"• النظام الوهمي: {'✅ مسموح' if settings.allow_simulation else '❌ غير مسموح'}\n"
            f"• وضع الصيانة: {'✅ نشط' if settings.maintenance_mode else '❌ غير نشط'}",
            reply_markup=menu,
            parse_mode="HTML"
        )
    finally:
        db.close()

async def toggle_trading_mode(callback: types.CallbackQuery):
    """تبديل وضع التداول الحقيقي"""
    db = next(get_db())
    try:
        settings = get_system_settings(db)
        new_mode = not settings.real_trading_enabled
        update_system_settings(db, {"real_trading_enabled": new_mode})
        
        mode_text = "✅ تم تفعيل التداول الحقيقي" if new_mode else "⛔ تم تعطيل التداول الحقيقي"
        await callback.answer(mode_text)
        await show_control_panel(callback.message)
    finally:
        db.close()

async def toggle_simulation_mode(callback: types.CallbackQuery):
    """تبديل السماح بالنظام الوهمي"""
    db = next(get_db())
    try:
        settings = get_system_settings(db)
        new_mode = not settings.allow_simulation
        update_system_settings(db, {"allow_simulation": new_mode})
        
        mode_text = "✅ تم السماح بالنظام الوهمي" if new_mode else "⛔ تم منع النظام الوهمي"
        await callback.answer(mode_text)
        await show_control_panel(callback.message)
    finally:
        db.close()

async def toggle_maintenance_mode(callback: types.CallbackQuery):
    """تبديل وضع الصيانة"""
    db = next(get_db())
    try:
        settings = get_system_settings(db)
        new_mode = not settings.maintenance_mode
        update_system_settings(db, {"maintenance_mode": new_mode})
        
        mode_text = "🔧 تم تفعيل وضع الصيانة" if new_mode else "⚙️ تم تعطيل وضع الصيانة"
        await callback.answer(mode_text)
        await show_control_panel(callback.message)
    finally:
        db.close()

def register_handlers(dp):
    """تسجيل جميع معالجات الأحداث"""
    dp.register_message_handler(
        show_control_panel,
        lambda msg: msg.from_user.id in SystemConfig.ADMIN_IDS,
        commands=["control"],
        state="*"
    )
    dp.register_callback_query_handler(
        toggle_trading_mode,
        lambda c: c.data == "toggle_real_trading",
        state="*"
    )
    dp.register_callback_query_handler(
        toggle_simulation_mode,
        lambda c: c.data == "toggle_simulation",
        state="*"
    )
    dp.register_callback_query_handler(
        toggle_maintenance_mode,
        lambda c: c.data == "toggle_maintenance",
        state="*"
    )
