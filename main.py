import asyncio
import logging
from core.config import TELEGRAM_BOT_TOKEN, ADMIN_TELEGRAM_ID
from core.logger import get_logger
from telegram_bot.bot import dp, bot
from trading.arbitrage import start_arbitrage_loop

logger = get_logger(__name__)

async def main():
    logger.info("Starting up the Arbitrage Bot...")

    # Set up the bot and its handlers
    bot_task = asyncio.create_task(dp.start_polling(bot))

    # Set up the arbitrage trading loop
    arb_task = asyncio.create_task(start_arbitrage_loop())

    # Wait for both tasks to complete
    await asyncio.gather(arb_task, bot_task)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Shutting down gracefully...')
