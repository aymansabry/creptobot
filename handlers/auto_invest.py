from aiogram import Router, types
from services.deal_executor import start_auto_invest
from database.crud import register_auto_invest
from utils.validators import is_valid_amount

router = Router()

@router.message(lambda msg: msg.text == "🚀 استثمار تلقائي")
async def handle_auto_invest(msg: types.Message):
    await msg.answer("💵 أدخل المبلغ الذي تريد استثماره تلقائيًا (USDT):")

@router.message(lambda msg: is_valid_amount(msg.text))
async def process_auto_invest(msg: types.Message):
    amount = float(msg.text)
    await register_auto_invest(msg.from_user.id, amount)
    await start_auto_invest(user_id=msg.from_user.id, amount=amount)
    await msg.answer(f"✅ تم تفعيل استثمار تلقائي بمبلغ {amount} USDT.")
