from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from services.trading import execute_trade

async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    amount = 100  # ثابت مؤقتًا
    result = await execute_trade(user_id, amount)
    await update.message.reply_text(f"✅ تم تنفيذ الصفقة. الناتج: {result:.2f} USDT")

trade_handler = CommandHandler("trade", trade)