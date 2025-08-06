from aiogram import types
from aiogram.dispatcher import FSMContext
from db.crud import get_system_settings, update_system_settings
from templates.menu_templates import admin_control_menu

async def show_control_panel(message: types.Message):
    settings = await get_system_settings()
    menu = await admin_control_menu(settings)
    await message.answer("لوحة تحكم النظام:", reply_markup=menu)

async def toggle_trading_mode(callback: types.CallbackQuery):
    settings = await get_system_settings()
    new_mode = not settings.real_trading_enabled
    await update_system_settings({"real_trading_enabled": new_mode})
    
    mode_text = "فعّال" if new_mode else "معطّل"
    await callback.answer(f"وضع التداول الحقيقي الآن {mode_text}")

async def toggle_simulation_mode(callback: types.CallbackQuery):
    settings = await get_system_settings()
    new_mode = not settings.allow_simulation
    await update_system_settings({"allow_simulation": new_mode})
    
    mode_text = "مسموح" if new_mode else "غير مسموح"
    await callback.answer(f"النظام الوهمي الآن {mode_text}")
