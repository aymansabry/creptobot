from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.config import SystemConfig

async def wallet_type_menu(settings):
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if settings.allow_simulation:
        keyboard.add(InlineKeyboardButton(
            text="🔄 محفظة تجريبية",
            callback_data="wallet_type:simulation"
        ))
    
    if settings.real_trading_enabled:
        keyboard.add(InlineKeyboardButton(
            text="💵 محفظة حقيقية",
            callback_data="wallet_type:real"
        ))
    
    return keyboard

async def admin_control_menu(settings):
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(
            text=f"{'✅' if settings.real_trading_enabled else '❌'} التداول الحقيقي",
            callback_data="toggle_real_trading"
        ),
        InlineKeyboardButton(
            text=f"{'✅' if settings.allow_simulation else '❌'} النظام الوهمي",
            callback_data="toggle_simulation"
        )
    )
    
    return keyboard
