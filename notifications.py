from settings import BOT_TOKEN, OWNER_ID
from aiogram import Bot
import requests

bot = Bot(token=BOT_TOKEN)

async def notify_user(telegram_id: int, text: str):
    try:
        await bot.send_message(telegram_id, text)
    except Exception as e:
        print('notify_user error', e)

async def notify_owner(text: str):
    await notify_user(OWNER_ID, text)

def webhook_notify(url: str, payload: dict):
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print('webhook error', e)
