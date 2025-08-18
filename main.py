from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import Config
import logging
import asyncio
from arbitrage import ArbitrageEngine  # افترضنا وجود ملف arbitrage.py بالخوارزميات

# إعداد نظام التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.arbitrage_engine = ArbitrageEngine()
        self.user_sessions = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            self.user_sessions[user_id] = {'active': True}
            
            keyboard = [
                [InlineKeyboardButton("🔄 ربط الحسابات", callback_data='connect')],
                [InlineKeyboardButton("📊 الإحصائيات", callback_data='stats')],
                [InlineKeyboardButton("⚡ تشغيل المراجحة", callback_data='start_arbitrage')],
                [InlineKeyboardButton("🛑 إيقاف المراجحة", callback_data='stop_arbitrage')]
            ]
            await update.message.reply_text(
                "مرحباً بك في بوت المراجحة الآلية\nاختر من القائمة:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Error in start: {e}")

    async def handle_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()
            user_id = query.from_user.id
            
            if query.data == 'connect':
                await self.show_exchanges_menu(query)
                
            elif query.data == 'stats':
                await self.show_stats(query, user_id)
                
            elif query.data == 'start_arbitrage':
                await self.start_arbitrage(query, user_id)
                
            elif query.data == 'stop_arbitrage':
                await self.stop_arbitrage(query, user_id)
                
            elif query.data == 'back_main':
                await self.show_main_menu(query)
                
            elif query.data.startswith('connect_'):
                exchange = query.data.split('_')[1]
                await self.connect_exchange(query, user_id, exchange)
                
            elif query.data == 'refresh_stats':
                await self.refresh_stats(query, user_id)

        except Exception as e:
            logger.error(f"Error in handle_buttons: {e}")

    async def show_exchanges_menu(self, query):
        keyboard = [
            [InlineKeyboardButton("بينانس", callback_data='connect_binance')],
            [InlineKeyboardButton("كوكوين", callback_data='connect_kucoin')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='back_main')]
        ]
        await query.edit_message_text(
            text="اختر المنصة لربط الحساب:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def show_stats(self, query, user_id):
        stats = self.arbitrage_engine.get_user_stats(user_id)
        stats_text = f"📊 إحصائيات المراجحة:\n\n"
        stats_text += f"🔄 صفقات اليوم: {stats['today_trades']}\n"
        stats_text += f"💰 أرباح اليوم: {stats['today_profit']} USDT\n"
        stats_text += f"📈 أفضل صفقة: {stats['best_trade']} USDT\n"
        stats_text += f"⚡ الحالة: {'🟢 نشط' if stats['is_active'] else '🔴 متوقف'}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data='refresh_stats')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='back_main')]
        ]
        await query.edit_message_text(
            text=stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def start_arbitrage(self, query, user_id):
        success, message = await self.arbitrage_engine.start(user_id)
        
        if success:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='back_main')]]
            await query.edit_message_text(
                text=f"✅ تم تشغيل المراجحة الآلية\n{message}",
                reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            keyboard = [[InlineKeyboardButton("إعدادات الحساب", callback_data='connect')]]
            await query.edit_message_text(
                text=f"⚠️ خطأ: {message}",
                reply_markup=InlineKeyboardMarkup(keyboard))

    async def stop_arbitrage(self, query, user_id):
        success, message = await self.arbitrage_engine.stop(user_id)
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='back_main')]]
        await query.edit_message_text(
            text=f"🛑 تم إيقاف المراجحة الآلية\n{message}",
            reply_markup=InlineKeyboardMarkup(keyboard))

    async def connect_exchange(self, query, user_id, exchange):
        # هنا نربط مع API المنصة الفعلي
        connect_url = self.arbitrage_engine.get_auth_url(exchange)
        
        keyboard = [
            [InlineKeyboardButton("🔗 ربط الحساب", url=connect_url)],
            [InlineKeyboardButton("✅ تم الربط", callback_data=f'verify_{exchange}')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='connect')]
        ]
        await query.edit_message_text(
            text=f"لربط حساب {exchange}:\n1. سجل الدخول عبر الزر\n2. أذن للوصول\n3. اضغط 'تم الربط'",
            reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_main_menu(self, query):
        keyboard = [
            [InlineKeyboardButton("🔄 ربط الحسابات", callback_data='connect')],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data='stats')],
            [InlineKeyboardButton("⚡ تشغيل المراجحة", callback_data='start_arbitrage')],
            [InlineKeyboardButton("🛑 إيقاف المراجحة", callback_data='stop_arbitrage')]
        ]
        await query.edit_message_text(
            text="القائمة الرئيسية:",
            reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def refresh_stats(self, query, user_id):
        await self.show_stats(query, user_id)

def main():
    bot = TradingBot()
    
    app = Application.builder().token(Config.BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CallbackQueryHandler(bot.handle_buttons))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()