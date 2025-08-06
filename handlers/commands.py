from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router(name="commands")

def main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(
        types.KeyboardButton(text="💰 إنشاء محفظة"),
        types.KeyboardButton(text="📊 عرض الصفقات"),
        types.KeyboardButton(text="👤 حسابي")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "مرحباً بك في بوت التداول الذكي! 🚀",
        reply_markup=main_keyboard()
    )

__all__ = ['router']
