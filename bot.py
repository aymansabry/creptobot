# bot.py
import os, logging, asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import start, button_handler
from handlers import get_user_by_telegram_id
from database import init_pool, query
from arbitrage import execute_arbitrage_for_user
from notifications import send_admin_alert
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# health check job
def health_check():
    try:
        # quick DB query
        r = query("SELECT 1 as ok", (), fetchone=True)
        if not r:
            send_admin_alert("Health Check Failed", "DB returned no response")
    except Exception as e:
        send_admin_alert("Health Check Error", str(e))

async def run_arbitrage_job():
    users = query("SELECT * FROM users WHERE is_active=TRUE")
    for u in users:
        try:
            execute_arbitrage_for_user(u)
        except Exception as e:
            logging.exception("user arbitrage fail %s", e)
            send_admin_alert("Arbitrage loop error", str(e))

async def start_bot():
    init_pool()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    # other command handlers (defined in handlers module) should be added similarly

    # scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(health_check, 'interval', minutes=int(os.getenv("HEALTH_INTERVAL_MIN", "2")))
    scheduler.add_job(lambda: asyncio.create_task(run_arbitrage_job()), 'interval', minutes=int(os.getenv("ARBITRAGE_INTERVAL_MIN", "5")))
    scheduler.start()

    logging.info("Bot starting...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(start_bot())
