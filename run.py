import asyncio
import logging
import uvicorn

from fastapi import FastAPI
from telegram_bot.bot import app as telegram_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = FastAPI()

@api.get("/")
def root():
    return {"status": "ok", "message": "Bot running"}

async def start_telegram():
    """تشغيل بوت التليجرام داخل نفس الـloop"""
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()

async def main():
    # شغل بوت التليجرام + fastapi في نفس الوقت
    task_telegram = asyncio.create_task(start_telegram())
    config = uvicorn.Config(api, host="0.0.0.0", port=8080, log_level="info")
    server = uvicorn.Server(config)
    task_api = asyncio.create_task(server.serve())

    await asyncio.gather(task_telegram, task_api)

if __name__ == "__main__":
    asyncio.run(main())
