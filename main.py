import asyncio
import logging
import os
from telegram.ext import Application
from src.handlers import setup_handlers
from src.db import init_db

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

async def main():
    await init_db()

    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    setup_handlers(app)

    logger.info("✅ البوت يعمل الآن...")
    await app.run_polling()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(main())
        else:
            loop.run_until_complete(main())
    except RuntimeError:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(main())
