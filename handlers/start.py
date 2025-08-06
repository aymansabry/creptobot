from aiogram import types, Router
from keyboards.main import main_menu
from database.users import create_user_if_not_exists

router = Router()

@router.message(commands=["start"])
async def start_handler(message: types.Message):
    await create_user_if_not_exists(message.from_user.id)
    await message.answer("👋 أهلاً بك في بوت التداول الذكي.\nاختر من القائمة:", reply_markup=main_menu)
