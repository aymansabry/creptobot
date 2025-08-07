import hashlib
from datetime import datetime

class SecurityManager:
    @staticmethod
    def encrypt_data(data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(key: str) -> bool:
        # تطبيق التحقق من المفاتيح
        return True
    
    @staticmethod
    def check_trade_time() -> bool:
        # التحقق من أوقات التداول المسموحة
        hour = datetime.now().hour
        return 0 <= hour < 22
