from aiogram import Router, types
from support.tickets import create_ticket

router = Router()

@router.message(lambda msg: msg.text == "🆘 دعم فني")
async def support_start(msg: types.Message):
    await msg.answer("✍️ أرسل مشكلتك أو استفسارك:")
    
@router.message()
async def support_message(msg: types.Message):
    await create_ticket(user_id=msg.from_user.id, text=msg.text)
    await msg.answer("✅ تم استلام رسالتك، سيرد عليك فريق الدعم قريبًا.")
