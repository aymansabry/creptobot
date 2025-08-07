from aiogram import Router, types
from services.deal_executor import execute_manual_deal
from utils.validators import is_valid_amount

router = Router()

@router.message(lambda msg: msg.text == "📊 صفقة يدوية")
async def manual_start(msg: types.Message):
    await msg.answer("💵 أدخل المبلغ لتنفيذ صفقة فورية (USDT):")

@router.message(lambda msg: is_valid_amount(msg.text))
async def process_manual(msg: types.Message):
    amount = float(msg.text)
    result = await execute_manual_deal(msg.from_user.id, amount)
    await msg.answer(f"📈 النتيجة: {result}")
