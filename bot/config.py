iimport os

class Config:
    # إعدادات обязательные
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')  # توكن البوت
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite')  # auto-convert for Railway
    
    # تحويل رابط PostgreSQL إذا لزم الأمر
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_TOKEN:
            raise ValueError("يجب تعيين TELEGRAM_TOKEN في متغيرات البيئة")

# التحقق التلقائي عند الاستيراد
Config.validate()
