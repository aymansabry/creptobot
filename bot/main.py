import logging
from telegram.ext import Application
from bot.handlers import setup_handlers
from bot.config import Config
import os

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BotRunner:
    def __init__(self):
        self.application = None

    async def start(self):
        """Initialize and start the bot"""
        try:
            self.application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
            setup_handlers(self.application)
            
            # Check for existing webhook
            if await self.application.bot.get_webhook_info():
                await self.application.bot.delete_webhook()
            
            logger.info("Starting bot in polling mode...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
        except Exception as e:
            logger.error(f"Bot startup failed: {e}")
            await self.shutdown()
            raise

    async def shutdown(self):
        """Clean shutdown"""
        if self.application:
            logger.info("Stopping bot gracefully...")
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

def main():
    runner = BotRunner()
    
    # Handle Railway's process management
    if os.getenv('RAILWAY_ENVIRONMENT'):
        import asyncio
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(runner.start())
            loop.run_forever()
        except KeyboardInterrupt:
            loop.run_until_complete(runner.shutdown())
        finally:
            loop.close()
    else:
        import asyncio
        asyncio.run(runner.start())

if __name__ == '__main__':
    main()
