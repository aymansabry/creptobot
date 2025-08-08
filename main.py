import asyncio
import logging
from telegram.ext import ApplicationBuilder

from src.handlers import setup_handlers
from src.db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    init_db()
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()
    setup_handlers(app)
    logger.info("✅ البوت يعمل الآن...")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "already running" in str(e):
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.get_event_loop().run_until_complete(main())
        else:
            raise
