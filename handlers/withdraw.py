from aiogram import Router, types
from database.crud import request_withdrawal
from utils.validators import is_valid_wallet

router = Router()

@router.message(lambda msg: msg.text == "💸 سحب الأرباح")
async def withdraw(msg: types.Message):
    await msg.answer("🔗 أرسل عنوان محفظتك لاستلام الأرباح (TRC20):")

@router.message(lambda msg: is_valid_wallet(msg.text))
async def process_withdrawal(msg: types.Message):
    await request_withdrawal(msg.from_user.id, msg.text)
    await msg.answer("✅ تم تقديم طلب السحب، ستتم المعالجة خلال دقائق.")
