import os

# توكن البوت
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود في متغيرات البيئة")

# رابط قاعدة البيانات
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL غير موجود في متغيرات البيئة")

# النسبة الافتراضية لربح البوت (ممكن تتحمل لاحقاً من settings في قاعدة البيانات)
DEFAULT_BOT_FEE_PERCENT = float(os.getenv("BOT_FEE_PERCENT", "10"))
