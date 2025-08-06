from aiogram import types
from services.arbitrage.real_arbitrage import RealArbitrage
from services.payment.real_transfer import PaymentGateway
from config import config

arbitrage = RealArbitrage(config)
payment = PaymentGateway(config)

async def handle_real_deal(callback: types.CallbackQuery):
    deal_id = callback.data.split("_")[1]
    profit = await arbitrage.execute_real_trade(deal_id)
    await payment.distribute_profits(callback.from_user.id, profit)
    await callback.answer("✅ تم تنفيذ الصفقة بنجاح!")
