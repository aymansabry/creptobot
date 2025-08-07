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
from utils.logger import setup_logging
setup_logging()

from core.config import config
from handlers import (
    start,
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, trading.execute_trade))

def main():
    """بدء تشغيل البوت"""
    try:
        app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        setup_handlers(app)
        
        app.run_polling()
    except Exception as e:
        print(f"Failed to start bot: {str(e)}")
        raise

if __name__ == "__main__":
    main()
