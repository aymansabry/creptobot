from aiogram import Router, types, F
from services.binance_api import get_real_deals

router = Router()

@router.message(F.text == "📊 عرض الصفقات")
async def show_deals(message: types.Message):
    deals = await get_real_deals()
    builder = InlineKeyboardBuilder()
    
    for deal in deals[:3]:  # عرض أفضل 3 صفقات
        builder.add(types.InlineKeyboardButton(
            text=f"{deal['symbol']} - ربح {deal['profit']}%",
            callback_data=f"deal_{deal['id']}"
        ))
    
    await message.answer(
        "💎 أفضل الصفقات المتاحة:",
        reply_markup=builder.as_markup()
    )
