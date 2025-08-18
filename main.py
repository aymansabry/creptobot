from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import Config
import logging
from typing import Dict, List

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class ExchangeManager:
    """فئة لإدارة المنصات مضمنة في الملف الرئيسي"""
    def __init__(self):
        self.connected_exchanges: Dict[str, bool] = {}

    async def connect_exchange(self, exchange_name: str) -> bool:
        """ربط منصة تداول"""
        if exchange_name.lower() in Config.SUPPORTED_EXCHANGES:
            self.connected_exchanges[exchange_name] = True
            return True
        return False

class ArbitrageEngine:
    """فئة المراجحة مضمنة في الملف الرئيسي"""
    @staticmethod
    async def find_opportunities() -> List[str]:
        """البحث عن فرص المراجحة (بيانات تجريبية)"""
        # في التطبيق الحقيقي، هذه البيانات تأتي من APIs المنصات
        prices = {
            'binance': {'BTCUSDT': 50000, 'ETHUSDT': 3000},
            'kucoin': {'BTCUSDT': 50100, 'ETHUSDT': 2995}
        }
        
        opportunities = []
        for symbol in prices['binance']:
            for exchange in prices:
                if exchange != 'binance':
                    diff = abs(prices['binance'][symbol] - prices[exchange][symbol]) / prices['binance'][symbol] * 100
                    if diff >= Config.ARB_THRESHOLD:
                        opportunities.append(
                            f"{symbol}: {diff:.2f}% (Binance → {exchange.capitalize()})"
                        )
        return opportunities

# تهيئة المديرين
exchange_manager = ExchangeManager()
arb_engine = ArbitrageEngine()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض القائمة الرئيسية"""
    commands = """
📊 <b>الأوامر المتاحة:</b>

🔹 /start - عرض القائمة
🔹 /connect [exchange] - ربط منصة تداول
🔹 /arbitrage - البحث عن فرص مراجحة
🔹 /exchanges - عرض المنصات المتصلة
"""
    await update.message.reply_html(commands)

async def connect_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ربط منصة تداول"""
    try:
        exchange_name = context.args[0] if context.args else 'binance'
        if await exchange_manager.connect_exchange(exchange_name):
            await update.message.reply_text(f"✅ تم ربط منصة {exchange_name}")
        else:
            await update.message.reply_text("❌ المنصة غير مدعومة")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ في الربط: {str(e)}")

async def arbitrage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """البحث عن فرص المراجحة"""
    try:
        opportunities = await arb_engine.find_opportunities()
        if opportunities:
            await update.message.reply_text(
                "🔍 <b>فرص المراجحة:</b>\n\n" + "\n".join(opportunities),
                parse_mode='HTML'
            )
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