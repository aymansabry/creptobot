#core/trade_executor.py
import asyncio
from typing import Dict, Optional
from .exchange_api import ExchangeAPI
from .wallet_manager import WalletManager
from db.crud import create_trade_record
from db.models import Trade
from utils.logger import logger
from notifications.telegram_notifier import send_notification

class TradeExecutor:
    def __init__(self, binance_api: ExchangeAPI, kucoin_api: Optional[ExchangeAPI] = None):
        self.binance = binance_api
        self.kucoin = kucoin_api
        self.exchanges = {
            'binance': self.binance,
            'kucoin': self.kucoin if kucoin_api else None
        }

    async def execute_arbitrage(self, opportunity: Dict, user_id: int, amount: float) -> Dict:
        """
        تنفيذ صفقة المراجحة الكاملة
        """
        try:
            # 1. التحقق من الرصيد
            user_wallet = await WalletManager.get_user_wallet(user_id)
            if user_wallet.balances.get('USDT', 0) < amount:
                raise ValueError("Insufficient balance")

            # 2. التحقق من توفر بورصة الشراء
            if opportunity['buy_from'] not in self.exchanges or not self.exchanges[opportunity['buy_from']]:
                raise ValueError(f"Exchange {opportunity['buy_from']} not available")

            # 3. تنفيذ أمر الشراء
            buy_exchange = self.exchanges[opportunity['buy_from']]
            buy_order = await buy_exchange.create_order(
                symbol=opportunity['symbol'],
                order_type='market',
                side='buy',
                amount=amount / opportunity['buy_price']
            )

            # 4. التحقق من توفر بورصة البيع
            if opportunity['sell_to'] not in self.exchanges or not self.exchanges[opportunity['sell_to']]:
                raise ValueError(f"Exchange {opportunity['sell_to']} not available")

            # 5. تنفيذ أمر البيع
            sell_exchange = self.exchanges[opportunity['sell_to']]
            sell_order = await sell_exchange.create_order(
                symbol=opportunity['symbol'],
                order_type='market',
                side='sell',
                amount=buy_order['filled']
            )

            # 6. حساب الربح
            profit = (sell_order['filled'] * sell_order['price']) - (buy_order['filled'] * buy_order['price'])
            profit_percentage = (profit / (buy_order['filled'] * buy_order['price'])) * 100

            # 7. تحديث المحفظة
            await WalletManager.deposit_to_wallet(
                user_id=user_id,
                currency='USDT',
                amount=profit
            )

            # 8. خصم عمولة البوت (10%)
            bot_commission = profit * 0.1
            await WalletManager.transfer_to_main_wallet(
                user_id=user_id,
                amount=bot_commission,
                currency='USDT'
            )

            # 9. تسجيل الصفقة
            trade_record = await create_trade_record(
                user_id=user_id,
                symbol=opportunity['symbol'],
                buy_exchange=opportunity['buy_from'],
                sell_exchange=opportunity['sell_to'],
                amount=amount,
                buy_price=buy_order['price'],
                sell_price=sell_order['price'],
                profit=profit - bot_commission,
                commission=bot_commission,
                status='completed'
            )

            # 10. إرسال الإشعارات
            await send_notification(
                user_id=user_id,
                message=f"✅ تم تنفيذ الصفقة بنجاح\n"
                        f"📊 الرمز: {opportunity['symbol']}\n"
                        f"🛒 الشراء من: {opportunity['buy_from']}\n"
                        f"💰 سعر الشراء: {buy_order['price']}\n"
                        f"🏪 البيع في: {opportunity['sell_to']}\n"
                        f"💵 سعر البيع: {sell_order['price']}\n"
                        f"🎯 الربح الصافي: {profit - bot_commission:.2f} USDT\n"
                        f"⚖️ العمولة: {bot_commission:.2f} USDT"
            )

            return {
                'status': 'success',
                'trade_id': trade_record.id,
                'profit': profit - bot_commission,
                'commission': bot_commission
            }

        except Exception as e:
            logger.error(f"Trade execution failed: {str(e)}")
            await create_trade_record(
                user_id=user_id,
                symbol=opportunity.get('symbol', ''),
                status='failed',
                error=str(e)
            )
            raise
