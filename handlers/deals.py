from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router(name="deals")

@router.message(F.text == "📊 عرض الصفقات")
async def show_deals(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="BTC/USDT - ربح 2.5%", callback_data="deal_1"),
        types.InlineKeyboardButton(text="ETH/USDT - ربح 1.8%", callback_data="deal_2")
    )
    
    await message.answer(
        "💎 أفضل الصفقات المتاحة:",
        reply_markup=builder.as_markup()
    )

__all__ = ['router']
