from typing import Dict, Optional
from datetime import datetime, timedelta
from ai.market_analysis import MarketAnalyzer
from database.crud import get_db
from database.models import Trade, TradeStep
from exchange.binance import BinanceAPI
from utils.logger import logger

class TradeService:
    def __init__(self):
        self.analyzer = MarketAnalyzer()
        self.binance = BinanceAPI()
    
    async def execute_trade(self, user_id: int, opportunity: Dict) -> Dict:
        """
        تنفيذ صفقة استثمارية كاملة
        مع مراقبة المخاطر خلال التنفيذ
        """
        db = next(get_db())
        
        try:
            # 1. إنشاء سجل الصفقة في قاعدة البيانات
            trade = Trade(
                user_id=user_id,
                amount=opportunity['amount'],
                currency='USDT',
                status='pending',
                risk_level=opportunity['risk_score']
            )
            db.add(trade)
            db.commit()
            db.refresh(trade)
            
            # 2. تنفيذ خطوات الصفقة
            execution_result = await self._execute_trade_steps(trade.id, opportunity)
            
            # 3. تحديث حالة الصفقة
            if execution_result['success']:
                trade.status = 'active'
                trade.profit = execution_result['estimated_profit']
            else:
                trade.status = 'failed'
                trade.profit = 0
            
            db.commit()
            
            return {
                'success': execution_result['success'],
                'trade_id': trade.id,
                'message': execution_result['message'],
                'estimated_profit': execution_result['estimated_profit']
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"فشل تنفيذ الصفقة: {str(e)}")
            return {
                'success': False,
                'message': f"خطأ في تنفيذ الصفقة: {str(e)}"
            }
    
    async def _execute_trade_steps(self, trade_id: int, opportunity: Dict) -> Dict:
        """
        تنفيذ الخطوات الفعلية للصفقة
        مع مراقبة المخاطر في كل خطوة
        """
        db = next(get_db())
        steps = []
        estimated_profit = 0
        
        try:
            # الخطوة 1: الشراء من السوق الأول
            buy_result = await self.binance.create_order(
                symbol=opportunity['buy_symbol'],
                side='buy',
                amount=opportunity['amount'],
                price=opportunity['buy_price']
            )
            
            if not buy_result['success']:
                raise Exception("فشل في أمر الشراء")
            
            # تسجيل خطوة الشراء
            buy_step = TradeStep(
                trade_id=trade_id,
                step_type='buy',
                exchange='binance',
                currency_pair=opportunity['buy_symbol'],
                amount=opportunity['amount'],
                price=opportunity['buy_price']
            )
            db.add(buy_step)
            steps.append(buy_step)
            
            # الخطوة 2: التحويل بين المنصات (إذا لزم الأمر)
            if opportunity.get('transfer_required', False):
                transfer_result = await self._transfer_assets(
                    opportunity['buy_symbol'],
                    opportunity['amount']
                )
                
                if not transfer_result['success']:
                    raise Exception("فشل في التحويل بين المنصات")
                
                transfer_step = TradeStep(
                    trade_id=trade_id,
                    step_type='transfer',
                    exchange=opportunity['target_exchange'],
                    currency_pair=opportunity['buy_symbol'],
                    amount=opportunity['amount']
                )
                db.add(transfer_step)
                steps.append(transfer_step)
            
            # الخطوة 3: البيع في السوق الهدف
            sell_result = await self.binance.create_order(
                symbol=opportunity['sell_symbol'],
                side='sell',
                amount=opportunity['amount'],
                price=opportunity['sell_price']
            )
            
            if not sell_result['success']:
                raise Exception("فشل في أمر البيع")
            
            # تسجيل خطوة البيع
            sell_step = TradeStep(
                trade_id=trade_id,
                step_type='sell',
                exchange='binance',
                currency_pair=opportunity['sell_symbol'],
                amount=opportunity['amount'],
                price=opportunity['sell_price']
            )
            db.add(sell_step)
            steps.append(sell_step)
            
            # حساب الربح المقدر
            estimated_profit = (opportunity['sell_price'] - opportunity['buy_price']) * opportunity['amount']
            
            db.commit()
            
            return {
                'success': True,
                'message': "تم تنفيذ الصفقة بنجاح",
                'estimated_profit': estimated_profit,
                'steps': steps
            }
            
        except Exception as e:
            # في حالة الخطأ، نقوم بإلغاء أي خطوات تم تنفيذها
            await self._rollback_trade_steps(steps)
            raise e
    
    async def _transfer_assets(self, symbol: str, amount: float) -> Dict:
        """تنفيذ تحويل الأصول بين المنصات"""
        # هنا يتم تنفيذ التحويل الفعلي بين المنصات
        # هذا مثال مبسط، في الواقع يحتاج إلى تكامل مع واجهات المنصات
        
        return {
            'success': True,
            'message': "تم التحويل بنجاح"
        }
    
    async def _rollback_trade_steps(self, steps: list):
        """تراجع عن الخطوات المنفذة في حالة الفشل"""
        for step in reversed(steps):
            if step.step_type == 'buy':
                # إذا كنا قد اشترينا، نبيع بنفس الكمية
                await self.binance.create_order(
                    symbol=step.currency_pair,
                    side='sell',
                    amount=step.amount,
                    price=step.price * 0.99  # بيع بسعر أقل قليلاً لتجنب الخسارة
                )
            elif step.step_type == 'sell':
                # إذا كنا قد بعنا، نشتري بنفس الكمية
                await self.binance.create_order(
                    symbol=step.currency_pair,
                    side='buy',
                    amount=step.amount,
                    price=step.price * 1.01  # شراء بسعر أعلى قليلاً
                )
    
    async def monitor_and_close_trades(self):
        """مراقبة الصفقات النشطة وإغلاقها عند تحقيق الهدف أو الخسارة"""
        db = next(get_db())
        
        active_trades = db.query(Trade).filter(
            Trade.status == 'active'
        ).all()
        
        for trade in active_trades:
            try:
                # الحصول على أحدث بيانات السعر
                current_prices = await self.binance.get_all_prices()
                
                # تحليل حالة الصفقة
                analysis = await self.analyzer._check_trade_status({
                    'symbol': trade.steps[0].currency_pair,
                    'entry_price': trade.steps[0].price,
                    'amount': trade.steps[0].amount,
                    'position': 'long'
                })
                
                # إذا كانت هناك خسارة محتملة، نغلق الصفقة
                if analysis['potential_loss'] > 0:
                    await self._close_trade(trade, 'stopped', "إيقاف لحماية رأس المال")
                
                # إذا تحقق هدف الربح، نغلق الصفقة
                elif analysis['potential_profit'] >= trade.profit * 0.9:  # 90% من الربح المستهدف
                    await self._close_trade(trade, 'completed', "تحقق هدف الربح")
                
            except Exception as e:
                logger.error(f"خطأ في مراقبة الصفقة {trade.id}: {str(e)}")
    
    async def _close_trade(self, trade, status, reason):
        """إغلاق الصفقة وتحديث الحسابات"""
        db = next(get_db())
        
        try:
            # إذا كانت الصفقة لا تزال تحتوي على أصول، نبيعها
            if status == 'stopped':
                last_step = trade.steps[-1]
                if last_step.step_type != 'sell':
                    await self.binance.create_order(
                        symbol=last_step.currency_pair,
                        side='sell',
                        amount=last_step.amount
                    )
            
            # تحديث حالة الصفقة
            trade.status = status
            trade.end_time = datetime.utcnow()
            
            # حساب الربح/الخسارة الفعلية
            # (في الواقع الفعلي، يجب حساب هذا بناءً على الأسعار الفعلية)
            if len(trade.steps) >= 2:
                buy_step = trade.steps[0]
                sell_step = trade.steps[-1]
                trade.profit = (sell_step.price - buy_step.price) * buy_step.amount
            
            # تحديث رصيد المستخدم
            user = trade.user
            user.balance += trade.profit * 0.95  # خصم 5% عمولة
            
            db.commit()
            
            logger.info(f"تم إغلاق الصفقة {trade.id} بحالة {status}. السبب: {reason}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"فشل في إغلاق الصفقة {trade.id}: {str(e)}")
