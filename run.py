import asyncio
from api.app import app
import uvicorn
from telegram_bot.bot import run_telegram_bot
import threading

if __name__ == '__main__':
    # run telegram bot in separate thread
    t = threading.Thread(target=run_telegram_bot, daemon=True)
    t.start()
    uvicorn.run("api.app:app", host="0.0.0.0", port=8080, reload=False)
