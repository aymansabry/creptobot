import asyncio
from api.app import app as api_app
from telegram_bot.bot import app as tg_app
import uvicorn

async def start_telegram():
    await tg_app.initialize()
    await tg_app.start()
    await tg_app.updater.start_polling()

async def main():
    t = asyncio.create_task(start_telegram())
    config = uvicorn.Config(api_app, host='0.0.0.0', port=8080, log_level='info')
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == '__main__':
    asyncio.run(main())
