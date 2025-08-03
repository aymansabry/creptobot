from aiogram import Dispatcher, types
from bot.wallet import create_virtual_wallet, get_user_wallet
from bot.db import get_session
from bot.models import User

def register_handlers(dp: Dispatcher):
    @dp.message()
    async def handle_message(message: types.Message):
        session = get_session()
        user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
        if not user:
            wallet = create_virtual_wallet()
            user = User(telegram_id=message.from_user.id, wallet_address=wallet, country="unknown")
            session.add(user)
            session.commit()
            await message.answer(f"Welcome! Your wallet: {wallet}")
        else:
            await message.answer(f"Your wallet: {user.wallet_address}")
