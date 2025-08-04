from telegram.ext import Application
from config import Config
from handlers import setup_handlers
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    try:
        app = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        setup_handlers(app)
        logging.info("✅ تم تشغيل البوت بنجاح")
        app.run_polling()
    except Exception as e:
        logging.error(f"فشل التشغيل: {e}")

if __name__ == "__main__":
    main()
