import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, getcontext
from core.exchanges import Binance, KuCoin  # افترضنا وجود وحدات للتبادلات
from core.utilities import Logger
from telegram import Update
from telegram.ext import ContextTypes

logger = Logger(__name__)

class SpatialArbitrage:
    def __init__(self, config: dict):
        self.min_profit_threshold = Decimal(config.get('min_profit', 0.5))  # 0.5%
        self.max_trade_amount = Decimal(config.get('max_amount', 1000))
        self.exchanges = {
            'binance': Binance(config['binance']),
            'kucoin': KuCoin(config['kucoin'])
        }
        self.active = False
        self.current_opportunities = []

    async def analyze_markets(self, pairs: List[str]) -> List[dict]:
        """تحليل أزواج التداول بين البورصات"""
        opportunities = []
        
        for pair in pairs:
            try:
                binance_data = await self.exchanges['binance'].get_order_book(pair)
                kucoin_data = await self.exchanges['kucoin'].get_order_book(pair)
                
                if not binance_data or not kucoin_data:
                    continue

                # حساب أفضل فرص الشراء/البيع
                buy_price = Decimal(binance_data['bids'][0][0])
                sell_price = Decimal(kucoin_data['asks'][0][0])
                
                # حساب الرسوم
                binance_fee = Decimal('0.001')  # 0.1%
                kucoin_fee = Decimal('0.001')
                
                # حساب الربح الصافي
                gross_profit = sell_price - buy_price
                net_profit = gross_profit - (buy_price * binance_fee) - (sell_price * kucoin_fee)
                profit_percentage = (net_profit / buy_price) * 100
                
                if profit_percentage >= self.min_profit_threshold:
                    opportunity = {
                        'pair': pair,
                        'buy_exchange': 'binance',
                        'buy_price': float(buy_price),
                        'sell_exchange': 'kucoin',
                        'sell_price': float(sell_price),
                        'profit': float(profit_percentage),
                        'max_amount': self.calculate_max_amount(binance_data, kucoin_data)
                    }
                    opportunities.append(opportunity)
                    
            except Exception as e:
                logger.error(f"Error analyzing {pair}: {e}")
        
        self.current_opportunities = opportunities
        return opportunities

    def calculate_max_amount(self, binance_data: dict, kucoin_data: dict) -> float:
        """حساب أقصى كمية للتداول بناء على السيولة"""
        binance_amount = float(binance_data['bids'][0][1])
        kucoin_amount = float(kucoin_data['asks'][0][1])
        return min(binance_amount, kucoin_amount, float(self.max_trade_amount))

    async def execute_arbitrage(self, opportunity: dict) -> dict:
        """تنفيذ عملية المراجحة"""
        if not self.active:
            return {'status': 'error', 'message': 'المحرك غير نشط'}
        
        try:
            # تنفيذ أوامر الشراء والبيع
            buy_result = await self.exchanges[opportunity['buy_exchange']].create_order(
                symbol=opportunity['pair'],
                side='buy',
                amount=opportunity['amount'],
                price=opportunity['buy_price'])
            
            sell_result = await self.exchanges[opportunity['sell_exchange']].create_order(
                symbol=opportunity['pair'],
                side='sell',
                amount=opportunity['amount'],
                price=opportunity['sell_price'])
            
            return {
                'status': 'success',
                'profit': opportunity['profit'],
                'details': {
                    'buy': buy_result,
                    'sell': sell_result
                }
            }
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {'status': 'error', 'message': str(e)}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تشغيل المراجحة من خلال بوت التليجرام"""
        self.active = True
        await update.callback_query.edit_message_text(
            text="✅ تم تشغيل مراجحة الأسعار المكانية\nجاري البحث عن الفرص...")
        
        # بدء المسح الدوري
        while self.active:
            opportunities = await self.analyze_markets(['BTC/USDT', 'ETH/USDT', 'XRP/USDT'])
            
            if opportunities:
                message = "🔍 فرص مراجحة متاحة:\n\n"
                for opp in opportunities:
                    message += (
                        f"💰 {opp['pair']}\n"
                        f"شراء من {opp['buy_exchange']}: {opp['buy_price']}\n"
                        f"بيع على {opp['sell_exchange']}: {opp['sell_price']}\n"
                        f"الربح: {opp['profit']:.2f}%\n"
                        f"الكمية: {opp['max_amount']:.4f}\n\n"
                    )
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=message)
                
                # تنفيذ أفضل فرصة (اختياري)
                best_opp = max(opportunities, key=lambda x: x['profit'])
                await self.execute_arbitrage(best_opp)
            
            await asyncio.sleep(10)  # مسح كل 10 ثواني

    async def stop(self, update: Update):
        """إيقاف المراجحة من خلال بوت التليجرام"""
        self.active = False
        await update.callback_query.edit_message_text(
            text="🛑 تم إيقاف مراجحة الأسعار المكانية")

    def get_status(self) -> dict:
        """حالة المحرك الحالية"""
        return {
            'active': self.active,
            'last_opportunities': self.current_opportunities,
            'settings': {
                'min_profit': float(self.min_profit_threshold),
                'max_amount': float(self.max_trade_amount)
            }
        }