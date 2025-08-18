from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from config import Config
from core.arbitrage.spatial import SpatialArbitrage
import logging
import asyncio

# إعداد نظام التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.spatial_arbitrage = SpatialArbitrage(Config.ARBITRAGE_CONFIG)
        self.user_sessions = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            self.user_sessions[user_id] = {'active': True}
            
            keyboard = [
                [InlineKeyboardButton("🌍 المراجحة المكانية", callback_data='spatial_menu')],
                [InlineKeyboardButton("🔄 ربط الحسابات", callback_data='connect')],
                [InlineKeyboardButton("📊 الإحصائيات", callback_data='stats')],
                [InlineKeyboardButton("⚙️ الإعدادات", callback_data='settings')]
            ]
            
            await update.message.reply_text(
                "🚀 مرحباً بك في بوت المراجحة الآلية المتقدم\n"
                "اختر من القائمة:",
                reply_markup=InlineKeyboardMarkup(keyboard)
                
        except Exception as e:
            logger.error(f"Error in start: {e}")

    async def handle_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()
            user_id = query.from_user.id
            
            if query.data == 'spatial_menu':
                await self.show_spatial_menu(query)
                
            elif query.data == 'start_spatial':
                await self.spatial_arbitrage.start(update, context)
                
            elif query.data == 'stop_spatial':
                await self.spatial_arbitrage.stop(update)
                
            elif query.data == 'spatial_stats':
                stats = self.spatial_arbitrage.get_status()
                await self.show_spatial_stats(query, stats)
                
            elif query.data == 'connect':
                await self.show_exchanges_menu(query)
                
            elif query.data == 'stats':
                await self.show_main_stats(query, user_id)
                
            elif query.data == 'settings':
                await self.show_settings_menu(query)
                
            elif query.data == 'back_main':
                await self.show_main_menu(query)
                
            elif query.data.startswith('connect_'):
                exchange = query.data.split('_')[1]
                await self.connect_exchange(query, user_id, exchange)

        except Exception as e:
            logger.error(f"Error in handle_buttons: {e}")

    async def show_spatial_menu(self, query):
        status = self.spatial_arbitrage.get_status()
        status_text = "🟢 نشط" if status['active'] else "🔴 متوقف"
        
        keyboard = [
            [InlineKeyboardButton(f"⚡ تشغيل المراجحة ({status_text})", callback_data='start_spatial')],
            [InlineKeyboardButton("🛑 إيقاف المراجحة", callback_data='stop_spatial')],
            [InlineKeyboardButton("📈 إحصائيات المراجحة", callback_data='spatial_stats')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='back_main')]
        ]
        
        await query.edit_message_text(
            text="🌍 قائمة المراجحة المكانية:\n"
                 "المراجحة المكانية تستفيد من فروق الأسعار بين البورصات المختلفة",
            reply_markup=InlineKeyboardMarkup(keyboard))

    async def show_spatial_stats(self, query, stats):
        opportunities = stats.get('last_opportunities', [])
        stats_text = "📊 إحصائيات المراجحة المكانية:\n\n"
        stats_text += f"الحالة: {'🟢 نشط' if stats['active'] else '🔴 متوقف'}\n"
        stats_text += f"أدنى ربح مطلوب: {stats['settings']['min_profit']}%\n"
        stats_text += f"أقصى كمية: {stats['settings']['max_amount']} USDT\n\n"
        
        if opportunities:
            stats_text += "🔍 آخر الفرص المكتشفة:\n"
            for opp in opportunities[:3]:  # عرض فقط أفضل 3 فرص
                stats_text += (
                    f"\n💰 {opp['pair']}\n"
                    f"↗️ شراء من {opp['buy_exchange']}: {opp['buy_price']}\n"
                    f"↘️ بيع على {opp['sell_exchange']}: {opp['sell_price']}\n"
                    f"🔼 ربح: {opp['profit']:.2f}%\n"
                )
        else:
            stats_text += "لا توجد فرص مراجحة حديثة"
            
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data='spatial_stats')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='spatial_menu')]
        ]
        
        await query.edit_message_text(
            text=stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard))

    async def show_main_menu(self, query):
        keyboard = [
            [InlineKeyboardButton("🌍 المراجحة المكانية", callback_data='spatial_menu')],
            [InlineKeyboardButton("🔄 ربط الحسابات", callback_data='connect')],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data='stats')],
            [InlineKeyboardButton("⚙️ الإعدادات", callback_data='settings')]
        ]
        
        await query.edit_message_text(
            text="القائمة الرئيسية:",
            reply_markup=InlineKeyboardMarkup(keyboard))

    # باقي الدوال (show_exchanges_menu, connect_exchange, etc...) تبقى كما هي
    # مع إضافة التعديلات اللازمة لتعمل مع النظام الجديد

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل النصية"""
        try:
            message = update.message.text
            if message.startswith('/'):
                await update.message.reply_text("استخدم الأزرار للتحكم في البوت")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")

def main():
    bot = TradingBot()
    
    app = Application.builder().token(Config.BOT_TOKEN).build()
    
    # معالجات الأوامر
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CallbackQueryHandler(bot.handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # تشغيل البوت
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == '__main__':
    main()