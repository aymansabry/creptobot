import logging
from telegram.ext import ApplicationBuilder
from handlers.user_handler import start_handler

from db import init_db

logging.basicConfig(level=logging.INFO)

def main():
    # إنشاء الجداول إذا لم تكن موجودة
    init_db()

    app = ApplicationBuilder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    app.add_handler(start_handler)

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
