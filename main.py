from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import Config
import logging
from exchange import ExchangeManager  # نستورد من exchange.py الموجود لديك

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class ArbitrageEngine:
    """محرك المراجحة ضمن نفس الملف"""
    def __init__(self, exchange_manager):
        self.exchange_manager = exchange_manager

    async def find_opportunities(self):
        """البحث عن فرص المراجحة"""
        prices = {
            'binance': {'BTCUSDT': 50000, 'ETHUSDT': 3000},
            'kucoin': {'BTCUSDT': 50100, 'ETHUSDT': 2995}
        }
        
        opportunities = []
        for symbol in prices['binance']:
            price_diff = abs((prices['binance'][symbol] - prices['kucoin'][symbol]) / 
                           min(prices['binance'][symbol], prices['kucoin'][symbol])) * 100
            if price_diff >= Config.ARB_THRESHOLD:
                opportunities.append(f"{symbol}: {price_diff:.2f}%")
        
        return opportunities

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
"""
    await update.message.reply_html(commands)

async def arbitrage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء المراجحة"""
    try:
        opportunities = await arb_engine.find_opportunities()
        if opportunities:
            await update.message.reply_text(
                "🔍 فرص المراجحة:\n" + "\n".join(opportunities)
        else:
            await update.message.reply_text("⚠️ لا توجد فرص مراجحة حالياً")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ في المراجحة: {str(e)}")

def setup_bot():
    app = Application.builder().token(Config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("arbitrage", arbitrage))
    app.run_polling()

if __name__ == "__main__":
    setup_bot()