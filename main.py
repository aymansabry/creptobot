# main.py
import logging
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
import database
import handlers

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN missing in .env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    # init DB (creates tables)
    database.init_database()
    app = ApplicationBuilder().token(TOKEN).build()
    handlers.register_handlers(app)
    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
