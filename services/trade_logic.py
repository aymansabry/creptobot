# project_root/services/trade_logic.py

import asyncio
from db import crud
from db.database import async_session
from services.ai_engine import AIEngine
from services.trade_executor import TradeExecutor
from services.wallet_manager import WalletManager
from core.config import settings
from datetime import datetime

class TradeLogic:
    def __init__(self, bot):
        self.ai_engine = AIEngine()
        self.trade_executor = TradeExecutor()
        self.wallet_manager = WalletManager()
        self.bot = bot

    async def execute_single_trade(self, user_id: int):
        """Executes a single manual trade for a user."""
        async with async_session() as db_session:
            wallet = await crud.get_wallet_by_user_id(db_session, user_id)
            if not wallet or wallet.balance_usdt < 1.0:
                return "insufficient_balance"

            # 1. AI Signal Generation (for a spot trade example)
            market_data = {
                'symbol': 'BTC/USDT', # Placeholder for a real symbol from market data feed
                'price': 65000,
                'volume_24h': 1000000000
            }
            signal = await self.ai_engine.generate_signal(market_data, 'spot')

            if signal.get('action') == 'buy':
                amount_to_trade = signal.get('amount', 1.0)
                if amount_to_trade > wallet.balance_usdt:
                    amount_to_trade = wallet.balance_usdt

                # 2. Execute the trade
                trade_result = await self.trade_executor.execute_order('binance', 'BTC/USDT', 'market', 'buy', amount_to_trade)
                if trade_result:
                    # 3. Record the trade in the database
                    trade_data = {
                        'wallet_id': wallet.id,
                        'symbol': 'BTC/USDT',
                        'exchange': 'binance',
                        'entry_price': trade_result['price'],
                        'amount': trade_result['amount'],
                        'type': 'spot',
                        'is_demo': False
                    }
                    new_trade = await crud.create_trade(db_session, trade_data)
                    await self.bot.send_message(user_id, f"✅ تم تنفيذ صفقة شراء ناجحة على {new_trade.symbol} بسعر {new_trade.entry_price}")
                    await self.bot.send_message(settings.ADMIN_ID, f"🆕 صفقة جديدة: المستخدم {user_id} اشترى {new_trade.amount} من {new_trade.symbol}")
                    
                    # This is where a sell signal would be generated and executed later
                    # await self.execute_sell_trade(new_trade.id, new_trade.amount, new_trade.entry_price)

            return "success"

    async def continuous_trading_loop(self, user_id: int):
        """Continuous loop for automated trading."""
        while True:
            async with async_session() as db_session:
                wallet = await crud.get_wallet_by_user_id(db_session, user_id)
                if not wallet or not wallet.is_continuous_trading:
                    await self.bot.send_message(user_id, "🛑 تم إيقاف التداول المستمر.")
                    break
                
                # Check for open trades, if any, don't open new ones.
                open_trades = await crud.get_open_trades(db_session, wallet.id)
                if open_trades:
                    await asyncio.sleep(60) # Wait if there's an open trade
                    continue

                # 1. AI Signal Generation
                market_data = await self.get_market_data()
                signal = await self.ai_engine.generate_signal(market_data, 'arbitrage')

                if signal.get('action') == 'buy':
                    amount_to_trade = signal.get('amount', 1.0)
                    if amount_to_trade > wallet.balance_usdt:
                        amount_to_trade = wallet.balance_usdt

                    # 2. Execute the trade
                    trade_result = await self.trade_executor.execute_order(signal['exchange'], signal['symbol'], 'market', 'buy', amount_to_trade)

                    if trade_result:
                        # 3. Record the trade
                        trade_data = {
                            'wallet_id': wallet.id,
                            'symbol': signal['symbol'],
                            'exchange': signal['exchange'],
                            'entry_price': trade_result['price'],
                            'amount': trade_result['amount'],
                            'type': 'arbitrage',
                            'is_demo': False
                        }
                        new_trade = await crud.create_trade(db_session, trade_data)

                        # Wait and execute the sell side
                        await asyncio.sleep(30) # Await a bit for the price to be ready on the other exchange
                        
                        sell_exchange = 'kucoin' if signal['exchange'] == 'binance' else 'binance'
                        sell_price_data = await self.trade_executor.get_ticker_price(sell_exchange, signal['symbol'])
                        exit_price = sell_price_data['ask']

                        if exit_price > new_trade.entry_price:
                            profit = (exit_price - new_trade.entry_price) * new_trade.amount
                            await self.trade_executor.execute_order(sell_exchange, signal['symbol'], 'market', 'sell', new_trade.amount)
                            await crud.close_trade(db_session, new_trade.id, exit_price, profit)
                            await self.wallet_manager.distribute_profit(new_trade.id, user_id, profit, is_continuous=True)
                            await self.bot.send_message(user_id, f"💰 تم إغلاق صفقة رابحة! الربح: {profit:.2f} USDT")
                            await self.bot.send_message(settings.ADMIN_ID, f"🎉 صفقة مربحة للمستخدم {user_id}. الربح: {profit:.2f} USDT")

            await asyncio.sleep(60) # Main loop sleep
    
    async def get_market_data(self):
        """Simulates fetching real-time market data from exchanges."""
        binance_ticker = await self.trade_executor.get_ticker_price('binance', 'BTC/USDT')
        kucoin_ticker = await self.trade_executor.get_ticker_price('kucoin', 'BTC/USDT')

        return {
            'binance_price': binance_ticker.get('ask'),
            'kucoin_price': kucoin_ticker.get('ask'),
        }
