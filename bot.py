# bot.py
import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Imports from other files
from db import create_user, save_api_keys, get_user_api_keys, save_amount, get_amount, get_last_trades
from trading import start_arbitrage, stop_arbitrage, get_client_for_user
from ai_strategy import AIStrategy
from datetime import datetime

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ai = AIStrategy()

# ====== Inline Keyboards ======
def _kbd_main():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("💰 Start Trading", callback_data="start_trading"),
             InlineKeyboardButton("🛑 Stop Trading", callback_data="stop_trading")],
            [InlineKeyboardButton("📊 Market Status", callback_data="market_status"),
             InlineKeyboardButton("📜 Reports", callback_data="reports")],
        ]
    )

def _kbd_settings():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔑 Link Platforms", callback_data="link_api")],
            [InlineKeyboardButton("💵 Set Investment Amount", callback_data="set_amount")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_main")],
        ]
    )

# ====== Command Handlers ======
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await create_user(user.id)
    await update.message.reply_text(
        "✅ Registration successful.\nChoose from the menu:", reply_markup=_kbd_main()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Control buttons:\n"
        "Settings — Link platform or change amount\n"
        "Start Trading — Starts the bot with the saved amount\n"
        "Stop Trading — Stops the bot\n"
        "Market Status — OpenAI analysis\n"
        "Reports — Last recorded trades"
    )

# ====== Callback Query Handler (for inline buttons) ======
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # Settings
    if data == "settings":
        await query.edit_message_text("⚙️ Settings — Choose:", reply_markup=_kbd_settings())
        return

    if data == "back_main":
        await query.edit_message_text("✅ Returned to the main menu.", reply_markup=_kbd_main())
        return

    if data == "link_api":
        context.user_data["stage"] = "api_key"
        await query.edit_message_text("🔑 Send the API Key now (one line).")
        return

    if data == "set_amount":
        context.user_data["stage"] = "amount"
        await query.edit_message_text("💵 Send the investment amount in USD (e.g., 5).")
        return

    # Trading controls
    if data == "start_trading":
        amount = get_amount(user_id)
        if not amount:
            await query.edit_message_text("❌ You have not specified an amount yet. Go to Settings > Set Investment Amount.")
            return
        await query.edit_message_text(f"💰 Starting trading with amount: {amount} USDT\n(I will notify you of the results)")
        asyncio.create_task(start_arbitrage(user_id))
        return

    if data == "stop_trading":
        await stop_arbitrage(user_id)
        await query.edit_message_text("🛑 Trading has been stopped.")
        return

    # Market Status
    if data == "market_status":
        await query.edit_message_text("⏳ Analyzing the market, please wait...")
        try:
            client = await get_client_for_user(user_id)
        except ValueError:
            await query.edit_message_text("❌ You have not registered your Binance keys yet. Go to Settings.")
            return

        tickers = await client.get_all_tickers()
        sample = ", ".join([t["symbol"] for t in tickers[:40]])
        analysis = await asyncio.to_thread(lambda: ai.analyze({"sample_symbols": sample}))
        chunks = [analysis[i:i+800] for i in range(0, len(analysis), 800)]
        for ch in chunks:
            await query.message.reply_text(f"📊 OpenAI Advice:\n{ch}")
        await query.message.reply_text("✅ Analysis complete.", reply_markup=_kbd_main())
        return

    # Reports
    if data == "reports":
        trades = get_last_trades(user_id)
        if not trades:
            await query.edit_message_text("📜 No trades recorded yet.", reply_markup=_kbd_main())
            return
        text = "📜 Last Trades:\n"
        for t in trades[:10]:
            ts = getattr(t, "timestamp", None)
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if ts else ""
            text += f"• {t.pair} | Profit: {t.profit:.6f}$ | {ts_str}\n"
        await query.edit_message_text(text, reply_markup=_kbd_main())
        return

# ====== Message Handler (for text input) ======
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    stage = context.user_data.get("stage")

    if stage == "api_key":
        context.user_data["tmp_api_key"] = text
        context.user_data["stage"] = "api_secret"
        await update.message.reply_text("🗝️ Now send the API Secret:")
        return

    if stage == "api_secret":
        api_key = context.user_data.pop("tmp_api_key", None)
        api_secret = text
        try:
            await save_api_keys(user_id, api_key, api_secret)
            await update.message.reply_text("✅ Keys saved successfully.", reply_markup=_kbd_main())
        except Exception as e:
            await update.message.reply_text(f"❌ Error saving keys: {e}", reply_markup=_kbd_main())
        context.user_data["stage"] = None
        return

    if stage == "amount":
        try:
            val = float(text)
            if val <= 0:
                raise ValueError("Amount must be greater than 0")
            if val > 10000:
                await update.message.reply_text("⚠️ The maximum investment is 10000 USDT.", reply_markup=_kbd_main())
                context.user_data["stage"] = None
                return
            await save_amount(user_id, val)
            await update.message.reply_text(f"✅ Amount saved: {val} USDT", reply_markup=_kbd_main())
        except Exception:
            await update.message.reply_text("❌ Enter a valid amount (e.g., 5).", reply_markup=_kbd_main())
        context.user_data["stage"] = None
        return

    await update.message.reply_text("📌 Use the buttons or type /help to view commands.", reply_markup=_kbd_main())

# ====== Main runner ======
def main():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")

    app = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("Bot is now running...")
    app.run_polling(poll_interval=1.0)

if __name__ == "__main__":
    main()
