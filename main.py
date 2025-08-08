import asyncio
import logging
from telegram.ext import ApplicationBuilder

from handlers import setup_handlers
from database import init_db
from utils.logger import setup_logger

setup_logger()
logger = logging.getLogger(__name__)

async def main():
    await init_db()

    app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()
    setup_handlers(app)

    logger.info("✅ البوت يعمل الآن...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())