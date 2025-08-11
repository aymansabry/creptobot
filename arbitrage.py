from typing import Dict, Optional, Any, Union
from datetime import datetime
import asyncio
import logging
from services.exchange_api import BinanceAPI, KuCoinAPI
from config import Config

# إعداد التسجيل
logger = logging.getLogger(__name__)

class ArbitrageEngine:
    def __init__(self):
        self.binance = BinanceAPI()
        self.kucoin = KuCoinAPI()
        self.min_profit_percentage = 0.005  # 0.5%
        self.max_retries = 3
        self.timeout = 10  # ثانية

    async def find_opportunity(
        self,
        symbol: str,
        credentials: Dict[str, Dict[str, str]],
        retry_count: int = 0
    ) -> Optional[Dict[str, Union[float, str]]]:
        """
        البحث عن فرص مراجحة بين المنصات
        """
        try:
            binance_price = await asyncio.wait_for(
                self.binance.get_ticker_price(symbol, credentials['binance']),
                timeout=self.timeout
            )
            kucoin_price = await asyncio.wait_for(
                self.kucoin.get_ticker_price(symbol, credentials['kucoin']),
                timeout=self.timeout
            )

            if None in (binance_price, kucoin_price):
                logger.warning(f"لا يمكن الحصول على أسعار {symbol} من إحدى المنصات")
                return None

            opportunity = None
            spread = abs(binance_price - kucoin_price)

            # فرصة شراء من KuCoin وبيع في Binance
            if kucoin_price < binance_price * (1 - self.min_profit_percentage):
                opportunity = {
                    'symbol': symbol,
                    'buy_exchange': 'kucoin',
                    'sell_exchange': 'binance',
                    'buy_price': kucoin_price,
                    'sell_price': binance_price,
                    'spread': spread,
                    'potential_profit': binance_price - kucoin_price,
                    'profit_percentage': (binance_price - kucoin_price) / kucoin_price,
                    'direction': 'kucoin_to_binance'
                }

            # فرصة شراء من Binance وبيع في KuCoin
            elif binance_price < kucoin_price * (1 - self.min_profit_percentage):
                opportunity = {
                    'symbol': symbol,
                    'buy_exchange': 'binance',
                    'sell_exchange': 'kucoin',
                    'buy_price': binance_price,
                    'sell_price': kucoin_price,
                    'spread': spread,
                    'potential_profit': kucoin_price - binance_price,
                    'profit_percentage': (kucoin_price - binance_price) / binance_price,
                    'direction': 'binance_to_kucoin'
                }

            return opportunity

        except asyncio.TimeoutError:
            logger.warning("انتهت مهلة انتظار الحصول على الأسعار")
            if retry_count < self.max_retries:
                return await self.find_opportunity(symbol, credentials, retry_count + 1)
            return None

        except Exception as e:
            logger.error(f"خطأ في البحث عن فرص المراجحة: {str(e)}", exc_info=True)
            return None

    async def execute_trade(
        self,
        opportunity: Dict[str, Union[float, str]],
        amount: float,
        credentials: Dict[str, Dict[str, str]],
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        تنفيذ صفقة المراجحة
        """
        try:
            # محاكاة التنفيذ (في الإنتاج سيتم الاتصال بالمنصات فعلياً)
            if opportunity['direction'] == 'kucoin_to_binance':
                # 1. شراء من KuCoin
                # 2. بيع في Binance
                fee = amount * 0.001 * 2  # رسوم الشراء والبيع
                net_profit = (opportunity['potential_profit'] * amount) - fee
                
                result = {
                    'status': 'success',
                    'symbol': opportunity['symbol'],
                    'executed_amount': amount,
                    'buy_price': opportunity['buy_price'],
                    'sell_price': opportunity['sell_price'],
                    'realized_profit': net_profit,
                    'fees': fee,
                    'net_profit': net_profit,
                    'profit_percentage': (net_profit / amount) * 100,
                    'timestamp': datetime.now().isoformat(),
                    'details': {
                        'buy_exchange': opportunity['buy_exchange'],
                        'sell_exchange': opportunity['sell_exchange']
                    }
                }

            else:  # binance_to_kucoin
                # 1. شراء من Binance
                # 2. بيع في KuCoin
                fee = amount * 0.001 * 2
                net_profit = (opportunity['potential_profit'] * amount) - fee
                
                result = {
                    'status': 'success',
                    'symbol': opportunity['symbol'],
                    'executed_amount': amount,
                    'buy_price': opportunity['buy_price'],
                    'sell_price': opportunity['sell_price'],
                    'realized_profit': net_profit,
                    'fees': fee,
                    'net_profit': net_profit,
                    'profit_percentage': (net_profit / amount) * 100,
                    'timestamp': datetime.now().isoformat(),
                    'details': {
                        'buy_exchange': opportunity['buy_exchange'],
                        'sell_exchange': opportunity['sell_exchange']
                    }
                }

            logger.info(f"تم تنفيذ الصفقة بنجاح: {result}")
            return result

        except Exception as e:
            logger.error(f"فشل تنفيذ الصفقة: {str(e)}", exc_info=True)
            if retry_count < self.max_retries:
                return await self.execute_trade(opportunity, amount, credentials, retry_count + 1)
            
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def monitor_market(
        self,
        symbols: list,
        credentials: Dict[str, Dict[str, str]],
        callback: callable
    ) -> None:
        """
        مراقبة السوق المستمرة للفرص
        """
        while True:
            try:
                for symbol in symbols:
                    opportunity = await self.find_opportunity(symbol, credentials)
                    if opportunity:
                        await callback(opportunity)
                
                await asyncio.sleep(5)  # فحص كل 5 ثواني

            except Exception as e:
                logger.error(f"خطأ في مراقبة السوق: {str(e)}")
                await asyncio.sleep(10)  # انتظار 10 ثواني قبل إعادة المحاولة
