from db.models import TradeLog
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

class TradeExecutor:
    def __init__(self, binance_api, main_wallet_address):
        self.api = binance_api
        self.main_wallet_address = main_wallet_address
        self.logger = logging.getLogger(__name__)

    async def execute(self, session: AsyncSession, opportunity: dict, amount: float):
        try:
            buy_price = opportunity['buy_price']
            sell_price = opportunity['sell_price']
            symbol = opportunity['symbol']
            quantity = amount / buy_price

            await self.api.place_order(symbol, 'buy', quantity, buy_price)
            await self.api.place_order(symbol, 'sell', quantity, sell_price)

            gross_profit = (sell_price - buy_price) * quantity
            fee = gross_profit * 0.1
            net_profit = gross_profit - fee

            await self.api.transfer_fee(fee, self.main_wallet_address)

            trade = TradeLog(
                symbol=symbol,
                buy_exchange=opportunity['buy_from'],
                sell_exchange=opportunity['sell_to'],
                buy_price=buy_price,
                sell_price=sell_price,
                quantity=quantity,
                profit=net_profit,
                success=True,
                timestamp=datetime.utcnow()
            )
            session.add(trade)
            await session.commit()
            self.logger.info(f"Trade executed for {symbol} with net profit: {net_profit:.2f}")

        except Exception as e:
            await session.rollback()
            self.logger.exception("Trade execution failed")