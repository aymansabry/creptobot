from aiogram.types import InlineKeyboardButton

def colorize_button(text, success=True):
    emoji = "🟢" if success else "🔴"
    return InlineKeyboardButton(f"{emoji} {text}", callback_data="noop")