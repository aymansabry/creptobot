import asyncio
from bot import app as telegram_app
import uvicorn

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(telegram_app.run_polling())
    uvicorn.run("routes:app", host="0.0.0.0", port=8080)
