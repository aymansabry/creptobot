import os
from decouple import config
from typing import Dict, Any

class Config:
    """
    إعدادات التطبيق الرئيسية
    كل الإعدادات تتم عبر متغيرات البيئة لأسباب أمنية
    """
    
    # إعدادات بوت التليجرام
    TELEGRAM_TOKEN: str = config('TELEGRAM_TOKEN', default='')
    
    # إعدادات منصة بينانس
    BINANCE_API_KEY: str = config('BINANCE_API_KEY', default='')
    BINANCE_SECRET_KEY: str = config('BINANCE_SECRET_KEY', default='')
    
    # إعدادات قاعدة البيانات
    DATABASE_URL: str = config('DATABASE_URL', default='sqlite:///database.db')
    # تعديل رابط PostgreSQL ليتوافق مع Railway
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # إعدادات المحفظة
    OWNER_WALLET: str = config('OWNER_WALLET', default='')
    
    # إعدادات اللغة
    DEFAULT_LANGUAGE: str = config('DEFAULT_LANGUAGE', default='ar')  # ar أو en
    
    # إعدادات التداول
    MIN_INVESTMENT: float = config('MIN_INVESTMENT', default=1.0, cast=float)  # الحد الأدنى للاستثمار (USDT)
    MIN_PROFIT_PERCENT: float = config('MIN_PROFIT_PERCENT', default=3.0, cast=float)  # الحد الأدنى للربح %
    BOT_FEE_PERCENT: float = config('BOT_FEE_PERCENT', default=1.0, cast=float)  # عمولة البوت %
    
    # العملات المدعومة
    SUPPORTED_CURRENCIES: Dict[str, Any] = {
        'USDT': {'name': 'تيثير', 'decimal': 2},
        'BTC': {'name': 'بتكوين', 'decimal': 8},
        'ETH': {'name': 'إيثيريوم', 'decimal': 6},
        'BNB': {'name': 'بينانس كوين', 'decimal': 4},
        'SOL': {'name': 'سولانا', 'decimal': 4},
        'XRP': {'name': 'ريبل', 'decimal': 2}
    }
    
    # إعدادات التحديث التلقائي
    MARKET_UPDATE_INTERVAL: int = config('MARKET_UPDATE_INTERVAL', default=5, cast=int)  # دقائق
    TRADE_PROCESSING_INTERVAL: int = config('TRADE_PROCESSING_INTERVAL', default=60, cast=int)  # دقائق
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        التحقق من صحة الإعدادات الأساسية
        """
        required_configs = [
            cls.TELEGRAM_TOKEN,
            cls.BINANCE_API_KEY,
            cls.BINANCE_SECRET_KEY,
            cls.DATABASE_URL
        ]
        
        if not all(required_configs):
            missing = []
            if not cls.TELEGRAM_TOKEN:
                missing.append('TELEGRAM_TOKEN')
            if not cls.BINANCE_API_KEY:
                missing.append('BINANCE_API_KEY')
            if not cls.BINANCE_SECRET_KEY:
                missing.append('BINANCE_SECRET_KEY')
            
            raise ValueError(f"إعدادات البيئة المطلوبة مفقودة: {', '.join(missing)}")
        
        return True

# تحميل الإعدادات عند الاستيراد
try:
    Config.validate_config()
except ValueError as e:
    print(f"خطأ في الإعدادات: {e}")
    exit(1)
