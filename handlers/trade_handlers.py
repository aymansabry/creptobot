from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def trade_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in context.bot_data['admin_ids']:
        return await update.message.reply_text("❌ غير مصرح لك.")

    decision_maker = context.bot_data['decision_maker']
    trade_executor = context.bot_data['trade_executor']
    db_session = context.bot_data['db_session']

    symbols = ["BTC/USDT", "ETH/USDT"]
    opportunities = await decision_maker.get_top_opportunities(symbols)

    if not opportunities:
        return await update.message.reply_text("⚠️ لا توجد فرص تداول مناسبة الآن.")

    top_opportunity = opportunities[0]
    async with db_session() as session:
        await trade_executor.execute(session, top_opportunity, amount=50)

    await update.message.reply_text(f"✅ تم تنفيذ صفقة على {top_opportunity['symbol']} بنجاح.")

def setup_trade_handlers(app: Application):
    app.add_handler(CommandHandler("trade", trade_now))