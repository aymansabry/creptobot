from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os
import openai

router = Router()

admin_ids_str = os.getenv("TELEGRAM_ADMIN_IDS", "")
ADMIN_IDS = set()
if admin_ids_str:
    ADMIN_IDS = set(int(i) for i in admin_ids_str.split(",") if i.strip().isdigit())

class UserStates(StatesGroup):
    choosing_mode = State()
    entering_binance_api = State()
    entering_binance_secret = State()
    entering_kucoin_api = State()
    entering_kucoin_secret = State()
    entering_kucoin_passphrase = State()
    entering_investment_amount = State()
    entering_wallet_address = State()

def mode_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="فعلي 💰", callback_data="mode_live"),
            InlineKeyboardButton(text="وهمي 🧪", callback_data="mode_demo"),
        ]
    ])
    return keyboard

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "مرحبًا بك في بوت المراجحة التلقائية!\n"
        "اختر الوضع الذي تريد العمل به:",
        reply_markup=mode_keyboard()
    )
    await state.set_state(UserStates.choosing_mode)

@router.callback_query(F.data.startswith("mode_"))
async def process_mode_selection(callback: CallbackQuery, state: FSMContext):
    mode = callback.data.split("_")[
