# project_root/services/trade_logic.py

import asyncio
from db import crud
from db.database import async_session
from services.trade_executor import TradeExecutor
from services.ai_engine import AIEngine
from utils.constants import MESSAGES
import random

class TradeLogic:
    def __init__(self, bot):
        self.bot = bot
        self.trade_executor = TradeExecutor()
        self.ai_engine = AIEngine()
        self.running_loops = {}

    async def get_ai_trades(self):
        """Fetches a list of AI-recommended trades from the AI engine."""
        return await self.ai_engine.get_trade_recommendation()

    async def continuous_trading_loop(self, user_id: int):
        """Starts a continuous trading loop for a user based on AI recommendations."""
        if user_id in self.running_loops and self.running_loops[user_id]:
            return

        self.running_loops[user_id] = True
        
        await self.bot.send_message(
            chat_id=user_id,
            text=MESSAGES['continuous_trading_started']
        )
        
        try:
            while self.running_loops.get(user_id):
                async with async_session() as db_session:
                    wallet = await crud.get_wallet_by_user_id(db_session, user_id)
                    if not wallet or wallet.balance_usdt < 1.0:
                        await self.bot.send_message(chat_id=user_id, text=MESSAGES['insufficient_balance'])
                        break

                    open_trade = await crud.get_open_trade(db_session, user_id)
                    
                    if not open_trade:
                        # Fetch new AI recommendations to select from
                        recommendations = await self.get_ai_trades()
                        if recommendations:
                            selected_trade = random.choice(recommendations)
                            await self.execute_single_trade(user_id, selected_trade)
                            await asyncio.sleep(5)
                            open_trade = await crud.get_open_trade(db_session, user_id)

                    if open_trade:
                        await self.monitor_and_close_trade(open_trade, db_session)
                    
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass
        finally:
            self.running_loops.pop(user_id, None)
            
            async with async_session() as db_session:
                wallet = await crud.get_wallet_by_user_id(db_session, user_id)
                if wallet:
                    wallet.is_continuous_trading = False
                    await db_session.commit()
                    
            await self.bot.send_message(
                chat_id=user_id,
                text=MESSAGES['continuous_trading_deactivated']
            )

    async def execute_single_trade(self, user_id: int, trade_data: dict = None):
        """
        Executes a single trade. If trade_data is provided, it uses the AI recommendation.
        Otherwise, it falls back to a default trade.
        """
        async with async_session() as db_session:
            wallet = await crud.get_wallet_by_user_id(db_session, user_id)
            if not wallet or wallet.balance_usdt < 1.0:
                return "insufficient_balance"

            if trade_data:
                symbol = trade_data['symbol']
                exchange = trade_data['exchange']
                trade_amount = wallet.balance_usdt * 0.95
                
                ticker = await self.trade_executor.get_ticker_price(exchange, symbol)
                if not ticker:
                    await self.bot.send_message(chat_id=user_id, text=f"Error getting price for {symbol}.")
                    return "error"
                
                entry_price = ticker['ask']
                
                # Check for sufficient balance before executing the real order
                if trade_amount > wallet.balance_usdt:
                    await self.bot.send_message(chat_id=user_id, text=MESSAGES['insufficient_balance'])
                    return "insufficient_balance"

                await self.trade_executor.execute_order(exchange, symbol, 'market', 'buy', trade_amount / entry_price)
                
                await crud.create_trade(db_session, user_id, symbol, exchange, 'spot', trade_amount, entry_price)
                
                await self.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ تم فتح صفقة جديدة:\nالرمز: {symbol}\nسعر الدخول: {entry_price:.2f} USDT"
                )
                return "success"
            else:
                await self.execute_single_trade(user_id, {'symbol': "BTC/USDT", 'exchange': "binance"})

    async def monitor_and_close_trade(self, trade, db_session):
        current_ticker = await self.trade_executor.get_ticker_price(trade.exchange, trade.symbol)
        if not current_ticker:
            return

        current_price = current_ticker['bid']
        # This profit goal would be dynamically set by the AI recommendation
        profit_goal = 1.0
        profit_percentage = ((current_price - trade.entry_price) / trade.entry_price) * 100
        
        if profit_percentage >= profit_goal:
            profit_usdt = (current_price - trade.entry_price) * (trade.amount / trade.entry_price)
            commission_rate = 0.05
            commission_amount = profit_usdt * commission_rate
            net_profit = profit_usdt - commission_amount
            
            await self.trade_executor.execute_order(trade.exchange, trade.symbol, 'market', 'sell', trade.amount / trade.entry_price)

            await crud.close_trade(db_session, trade.id, current_price, net_profit)
            await crud.create_transaction(db_session, trade.user_id, 'profit', net_profit, trade.id)
            await crud.update_wallet_balance(db_session, trade.user_id, net_profit)
            
            await self.bot.send_message(
                chat_id=trade.user_id,
                text=f"""🎉 تم إغلاق الصفقة بنجاح!
الرمز: {trade.symbol}
سعر الخروج: {current_price:.2f} USDT
الربح: {profit_usdt:.2f} USDT
العمولة: {commission_amount:.2f} USDT
صافي الربح المحول إلى محفظتك: {net_profit:.2f} USDT
"""
            )

    def stop_continuous_trading(self, user_id: int):
        if user_id in self.running_loops:
            self.running_loops[user_id] = False
            return True
        return False
