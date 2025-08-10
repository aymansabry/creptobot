import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from settings import BOT_TOKEN, OWNER_ID, MODE
from database import SessionLocal
from models import User, APIKey
from utils import encrypt_text
from arbitrag import ArbEngine

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    session = SessionLocal()
    user = session.query(User).filter(User.telegram_id==message.from_user.id).first()
    if not user:
        role = 'owner' if message.from_user.id == OWNER_ID else 'client'
        user = User(telegram_id=message.from_user.id, role=role)
        session.add(user)
        session.commit()
    await message.reply(f'مرحبا! دورك: {user.role}. وضع التشغيل: {MODE}')

@dp.message(Command('add_apikey'))
async def cmd_add_apikey(message: types.Message):
    args = message.text.split()
    if len(args) < 4:
        await message.reply('استخدام: /add_apikey <exchange> <api_key> <api_secret> [passphrase]')
        return
    _, exchange, api_key, api_secret, *rest = args
    passphrase = rest[0] if rest else None
    session = SessionLocal()
    user = session.query(User).filter(User.telegram_id==message.from_user.id).first()
    if not user:
        await message.reply('سجل أولًا باستخدام /start')
        return
    enc_k = encrypt_text(api_key)
    enc_s = encrypt_text(api_secret)
    enc_p = encrypt_text(passphrase) if passphrase else None
    apikey = APIKey(user_id=user.id, exchange=exchange.lower(), api_key_encrypted=enc_k, api_secret_encrypted=enc_s, passphrase_encrypted=enc_p)
    session.add(apikey)
    session.commit()
    await message.reply('تم حفظ مفاتيح API (مشفّرة).')

@dp.message(Command('run'))
async def cmd_run(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.reply('غير مصرح')
        return
    await message.reply('Starting arb engine (background).')
    arb = ArbEngine()
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, arb.start_scheduler, 30)
    await message.reply('Engine started.')

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
