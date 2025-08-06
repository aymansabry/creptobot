from aiogram import types
from strategies.arbitrage import RealArbitrage
from services.payment.real_transfer import PaymentGateway

arbitrage = RealArbitrage(BinanceAPI(config.BINANCE_API_KEY, config.BINANCE_SECRET))
payment = PaymentGateway(config)

async def handle_real_deal(callback: types.CallbackQuery):
    deal_id = callback.data.split("_")[1]
    
    async for opportunity in arbitrage.scan_opportunities():
        if opportunity['id'] == deal_id:
            # تنفيذ الصفقة
            order = await arbitrage.api.execute_order({
                'symbol': opportunity['symbol'],
                'side': 'BUY',
                'type': 'MARKET',
                'quantity': 0.001  # مثال: 0.001 BTC
            })
            
            # توزيع الأرباح
            receipt = await payment.distribute_profits(
                user_wallet=callback.from_user.wallet,
                amount=opportunity['profit']
            )
            
            await callback.message.answer(
                f"✅ تم تنفيذ الصفقة بنجاح!\n"
                f"📊 الربح: {opportunity['profit']}%\n"
                f"🔗 تفاصيل التحويل: {receipt['txid']}"
            )
            break
