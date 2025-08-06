from aiogram import types
from services.binance.client import BinanceClient
from services.payment.tron_manager import TronManager
from config import config

binance = BinanceClient()
tron = TronManager()

async def handle_real_deal(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    try:
        # تنفيذ الصفقة (مثال)
        order = binance.create_order(
            symbol="BTCUSDT",
            side="BUY",
            type="MARKET",
            quantity=0.001
        )
        
        # تحويل الأرباح
        receipt = tron.send_usdt("USER_WALLET_ADDRESS", 10.0)
        
        await callback.answer("✅ تمت الصفقة بنجاح!")
    except Exception as e:
        await callback.answer(f"❌ خطأ: {str(e)}")
