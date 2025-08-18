from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import Config
import logging
from arbitrage import ArbitrageEngine
from exchange import ExchangeManager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# تهيئة المديرين
exchange_manager = ExchangeManager()
arb_engine = ArbitrageEngine(exchange_manager)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض القائمة الرئيسية"""
    commands = """
📊 <b>الأوامر المتاحة:</b>

🔹 /start - عرض القائمة الرئيسية
🔹 /connect - ربط منصات التداول
🔹 /arbitrage - بدء المراجحة الآلية
🔹 /portfolio - عرض محفظتك
🔹 /settings - ضبط إعدادات البوت
🔹 /help - المساعدة الفنية
"""
    await update.message.reply_html(commands)

async def connect_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ربط منصات التداول"""
    user_id = update.effective_user.id
    try:
        # هنا يتم ربط المنصات (يجب تطبيق المنطق الفعلي)
        await exchange_manager.connect_user_exchanges(user_id)
        await update.message.reply_text("✅ تم ربط المنصات بنجاح")
    except Exception as e:
        await update.message.reply_text(f"❌ فشل الربط: {str(e)}")

async def arbitrage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء المراجحة الآلية"""
    user_id = update.effective_user.id
    try:
        opportunities = await arb_engine.find_opportunities(user_id)
        if opportunities:
            msg = "🔍 <b>فرص المراجحة:</b>\n\n"
            msg += "\n".join([
                f"{opp['symbol']}: {opp['profit']}% ({opp['exchange1']} → {opp['exchange2']})"
                for opp in opportunities
            ])
            await update.message.reply_html(msg)
        else:
            await update.message.reply_text("⚠️ لا توجد فرص مراجحة حالياً")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ في المراجحة: {str(e)}")

def setup_bot():
    app = Application.builder().token(Config.BOT_TOKEN).build()
    
    # تسجيل الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("connect", connect_exchange))
    app.add_handler(CommandHandler("arbitrage", arbitrage))
    
    app.run_polling()

if __name__ == "__main__":
    setup_bot()