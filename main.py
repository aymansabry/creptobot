import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler
)

# تهيئة اللوغر الأساسي
from utils.logger import setup_logging
setup_logging()

# استيراد المكونات الأساسية
from core.config import config
from core.virtual_wallet import virtual_wallet
from core.trading_engine import TradingEngine

# استيراد handlers
from handlers.deposit import (
    start_deposit,
    receive_deposit_amount,
    verify_transaction,
    cancel_deposit,
    DEPOSIT_AMOUNT,
    DEPOSIT_CONFIRM
)
from handlers.trading import start_trading, execute_trade
from handlers.wallet import show_balance

# تهيئة محرك التداول
engine = TradingEngine()

async def start(update: Update, context: CallbackContext):
    """Start command handler"""
    user_id = str(update.effective_user.id)
    virtual_wallet.create_wallet(user_id)
    
    await update.message.reply_text(
        "🚀 مرحباً بكم في نظام التداول الآلي\n\n"
        f"رصيدك الحالي: {virtual_wallet.get_balance(user_id):.2f} USDT\n\n"
        "استخدم الأوامر التالية:\n"
        "/deposit - لإيداع الأموال\n"
        "/trade - لبدء التداول\n"
        "/balance - لعرض رصيدك"
    )

def main():
    """Start the bot"""
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Add conversation handler for deposits
    deposit_conv = ConversationHandler(
        entry_points=[CommandHandler('deposit', start_deposit)],
        states={
            DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_deposit_amount)],
            DEPOSIT_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_transaction)]
        },
        fallbacks=[CommandHandler('cancel', cancel_deposit)]
    )

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(deposit_conv)
    app.add_handler(CommandHandler("trade", start_trading))
    app.add_handler(CommandHandler("balance", show_balance))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, execute_trade))
    
    # Start the bot
    app.run_polling()

if __name__ == "__main__":
    main()
