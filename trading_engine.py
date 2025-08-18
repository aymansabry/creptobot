from binance import AsyncClient
from user_manager import UserManager
from config import Config
import logging

logger = logging.getLogger(__name__)

class TradingEngine:
    def __init__(self, user_id):
        self.user_id = user_id
        self.client = None
        
    async def initialize_client(self):
        """تهيئة العميل بشكل غير متزامن"""
        user_manager = UserManager()
        credentials = user_manager.get_user_credentials(self.user_id)
        if not credentials:
            raise Exception("لم يتم العثور على مفاتيح API للمستخدم")
            
        self.client = await AsyncClient.create(
            api_key=credentials['api_key'],
            api_secret=credentials['secret_key']
        )
        return self.client
    
    async def execute_order(self, symbol, side, amount):
        """تنفيذ الأمر بشكل غير متزامن"""
        if not self.client:
            await self.initialize_client()
            
        try:
            order = await self.client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quoteOrderQty=amount
            )
            return order
        except Exception as e:
            logger.error(f"Trade error: {str(e)}")
            raise