from aiogram import Dispatcher, types, F
from config import OWNER_TELEGRAM_ID

support_sessions = {}

async def support_entry(msg: types.Message):
    support_sessions[msg.from_user.id] = []
    await msg.answer("🆘 أرسل رسالتك وسنقوم بالرد عليك قريباً.")

async def support_message(msg: types.Message):
    if msg.from_user.id in support_sessions:
        await msg.forward(chat_id=OWNER_TELEGRAM_ID)

def register_support_handlers(dp: Dispatcher):
    dp.message.register(support_entry, F.text == "📞 الدعم الفني")
    dp.message.register(support_message)
