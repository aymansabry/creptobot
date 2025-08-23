from config import settings
from telegram import Bot
from db.session import AsyncSessionLocal
from db.models import User

bot = Bot(token=settings.telegram_bot_token) if settings.telegram_bot_token else None

async def send_user_message(user_id:int, text:str):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user or not user.telegram_chat_id:
            return False
        if not bot:
            return False
        try:
            bot.send_message(chat_id=int(user.telegram_chat_id), text=text)
            return True
        except Exception as e:
            print('tg err', e)
            return False

async def send_trade_report(user_id:int, trade_record:dict):
    text = f"تقرير الصفقة:\n{trade_record}"
    return await send_user_message(user_id, text)
