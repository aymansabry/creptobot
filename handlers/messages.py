from aiogram import types, Router
from database.investments import log_pending_investment
from utils.fake_wallet import generate_virtual_wallet_address

router = Router()

@router.message(lambda m: m.text and m.text.isdigit())
async def investment_amount_handler(message: types.Message):
    amount = float(message.text)
    wallet = generate_virtual_wallet_address()

    await log_pending_investment(user_id=message.from_user.id, amount=amount, wallet_address=wallet)
    
    await message.answer(
        f"📨 تم تسجيل طلبك.\n\n🔗 عنوان المحفظة الوهمية:\n`{wallet}`\n\n"
        "برجاء تحويل المبلغ وانتظر التحقق...",
        parse_mode="Markdown"
    )
