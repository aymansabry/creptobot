from aiogram import Router, types
from aiogram.filters import Command
from utils.buttons import main_menu
from database.crud import get_or_create_user

router = Router()

@router.message(Command("start"))
async def handle_start(msg: types.Message):
    user = await get_or_create_user(msg.from_user)
    welcome = f"👋 مرحبًا {msg.from_user.first_name}!\n\nأهلاً بك في بوت الاستثمار الذكي.\nاختر من القائمة:"
    await msg.answer(welcome, reply_markup=main_menu(user["role"]))
