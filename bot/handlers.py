from aiogram import Dispatcher, types
from aiogram.filters import CommandStart
from .wallet import get_user_wallet, create_virtual_wallet

async def start_handler(message: types.Message):
    user_id = message.from_user.id
    wallet = get_user_wallet(user_id)
    if wallet:
        await message.answer(f"🎉 مرحبًا مجددًا! محفظتك المسجلة: {wallet}")
    else:
        await message.answer("👋 مرحبًا! لم يتم ربط أي محفظة بعد.\nأرسل عنوان محفظتك لربطها.")

async def wallet_handler(message: types.Message):
    user_id = message.from_user.id
    address = message.text.strip()
    if address.startswith("0x") and len(address) >= 42:  # تحقق مبدئي من عنوان إيثيريوم
        create_virtual_wallet(user_id, address)
        await message.answer(f"✅ تم ربط محفظتك بنجاح: {address}")
    else:
        await message.answer("❌ عنوان المحفظة غير صالح. يرجى التأكد وإعادة الإرسال.")

def register_handlers(dp: Dispatcher):
    dp.message.register(start_handler, CommandStart())
    dp.message.register(wallet_handler)
