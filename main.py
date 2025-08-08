import asyncio
import logging
from core.config import load_env
from core.logger import setup_logger
from db.database import init_db
from handlers.user import user_handlers
from handlers.admin import admin_handlers
from handlers.common import common_handlers
from telegram.ext import Application

async def main():
    load_env()
    setup_logger()
    await init_db()

    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    user_handlers(app)
    admin_handlers(app)
    common_handlers(app)

    print("🤖 البوت يعمل الآن...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
