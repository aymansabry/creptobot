import os
from aiogram.utils.executor import start_webhook

WEBHOOK_URL = os.getenv("RAILWAY_STATIC_URL") + "/webhook"

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

if __name__ == "__main__":
    if config.is_production:
        start_webhook(
            dispatcher=dp,
            webhook_path="/webhook",
            on_startup=on_startup,
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8000))
    else:
        asyncio.run(dp.start_polling())
