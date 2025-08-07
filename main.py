import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler
)

# تهيئة النظام
from utils.logger import Logger
logger = Logger()

from core.config import config
from core.virtual_wallet import virtual_wallet
from core.trading_engine import TradingEngine

# استيراد ال handlers
from handlers import (
    deposit,
    trading,
    wallet
)

def setup_handlers(app):
    """إعداد جميع ال handlers"""
    # Deposit Conversation
    deposit_conv = ConversationHandler(
        entry_points=[CommandHandler('deposit', deposit.start_deposit)],
        states={
            deposit.DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit.receive_deposit_amount)],
            deposit.DEPOSIT_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit.verify_transaction)]
        },
        fallbacks=[CommandHandler('cancel', deposit.cancel_deposit)]
    )
    
    app.add_handler(CommandHandler("start", wallet.start))
    app.add_handler(deposit_conv)
    app.add_handler(CommandHandler("trade", trading.start_trading))
    app.add_handler(CommandHandler("balance", wallet.show_balance))

def main():
    """بدء تشغيل البوت"""
    try:
        app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        setup_handlers(app)
        
        logger.user.info("Starting bot application")
        app.run_polling()
    except Exception as e:
        log_error(f"Bot startup failed: {str(e)}", 'system')
        raise

if __name__ == "__main__":
    main()
