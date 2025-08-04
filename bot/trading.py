from datetime import datetime
import logging
from database import get_db_session, Trade, Transaction, Report
from config import Config
import ccxt
import pandas as pd
import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingEngine:
    def __init__(self):
        self.binance = self._init_exchange()
        self.scheduler = BackgroundScheduler()
        self._setup_scheduler()
    
    def _init_exchange(self):
        return ccxt.binance({
            'apiKey': Config.BINANCE_API_KEY,
            'secret': Config.BINANCE_SECRET_KEY,
            'enableRateLimit': True
        })
    
    def _setup_scheduler(self):
        # تحديث الفرص كل 5 دقائق
        self.scheduler.add_job(
            self.update_opportunities,
            'interval',
            minutes=5
        )
        
        # معالجة الاستثمارات المستمرة كل ساعة
        self.scheduler.add_job(
            self.process_continuous_investments,
            'interval',
            hours=1
        )
        
        self.scheduler.start()
    
    def update_opportunities(self):
        """تحديث قائمة الفرص الاستثمارية"""
        try:
            tickers = self.binance.fetch_tickers()
            usdt_pairs = {k: v for k, v in tickers.items() if k.endswith('/USDT')}
            
            df = pd.DataFrame.from_dict(usdt_pairs, orient='index')
            df['spread_pct'] = (df['ask'] - df['bid']) / df['bid'] * 100
            
            # تصفية الفرص المربحة
            min_profit = Config.MIN_PROFIT_PERCENT + Config.BOT_FEE_PERCENT
            self.opportunities = df[df['spread_pct'] >= min_profit]\
                                .sort_values('spread_pct', ascending=False)\
                                .head(10)\
                                .to_dict('records')
            
            logger.info(f"Updated opportunities: {len(self.opportunities)} found")
        except Exception as e:
            logger.error(f"Error updating opportunities: {e}")
    
    def execute_trade(self, user_id, trade_data):
        """تنفيذ صفقة استثمارية"""
        session = get_db_session()
        try:
            # تسجيل الصفقة
            trade = Trade(
                user_id=user_id,
                trade_type=trade_data.get('type', 'arbitrage'),
                buy_currency=trade_data['buy_currency'],
                sell_currency=trade_data['sell_currency'],
                buy_price=trade_data['buy_price'],
                sell_price=trade_data['sell_price'],
                amount=trade_data['amount'],
                profit=trade_data['profit'],
                fee=trade_data['fee'],
                status='completed',
                metadata={
                    'source': 'binance',
                    'strategy': 'arbitrage',
                    'risk_level': 'low'
                }
            )
            session.add(trade)
            
            # تسجيل المعاملة
            transaction = Transaction(
                user_id=user_id,
                transaction_type='investment',
                amount=trade_data['amount'],
                currency='USDT',
                status='completed',
                details=json.dumps({
                    'trade_id': trade.id,
                    'profit': trade_data['profit'],
                    'fee': trade_data['fee']
                })
            )
            session.add(transaction)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Trade execution failed: {e}")
            return False
        finally:
            session.close()
    
    def process_continuous_investments(self):
        """معالجة الاستثمارات المستمرة"""
        session = get_db_session()
        try:
            # جلب جميع الاستثمارات المستمرة النشطة
            investments = session.query(ContinuousInvestment)\
                               .filter_by(is_active=True)\
                               .all()
            
            for investment in investments:
                self._process_single_investment(investment)
            
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Continuous investment processing failed: {e}")
        finally:
            session.close()
    
    def _process_single_investment(self, investment):
        """معالجة استثمار مستمر واحد"""
        # ... (الكود السابق)
