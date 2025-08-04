from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)
from bot.database import get_db_session, User, Trade
from bot.trading import TradingEngine
from bot.analysis import MarketAnalyzer
from bot.messages import ARABIC_MESSAGES as MSG
from bot.config import Config
import logging

logger = logging.getLogger(__name__)

class Handlers:
    def __init__(self):
        self.trading_engine = TradingEngine()
        self.market_analyzer = MarketAnalyzer(self.trading_engine)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Professional start handler with user registration"""
        try:
            async with get_db_session() as session:
                user = update.effective_user
                
                # User registration logic
                if not await User.get(user.id, session):
                    new_user = User(
                        telegram_id=user.id,
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name
                    )
                    await session.add(new_user)
                    await session.commit()
                
                # Send welcome message
                keyboard = self._create_main_keyboard()
                await update.message.reply_text(
                    MSG['welcome'],
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"Start error: {e}")
            await self._send_error(update)

    def _create_main_keyboard(self):
        """Create professional keyboard layout"""
        return ReplyKeyboardMarkup(
            [
                ["📊 الفرص الاستثمارية", "💼 رصيدي"],
                ["📈 استثمار آلي", "📝 تقاريري"],
                ["⚙️ الإعدادات", "🆘 المساعدة"]
            ],
            resize_keyboard=True,
            input_field_placeholder="اختر خيارًا"
        )

    async def _send_error(self, update: Update):
        """Standard error handler"""
        await update.message.reply_text(
            MSG['error'],
            reply_markup=self._create_main_keyboard()
        )

def setup_handlers(application):
    """Professional handler registration"""
    handlers = Handlers()
    
    # Command handlers
    application.add_handler(CommandHandler("start", handlers.start))
    
    # Arabic commands
    application.add_handler(CommandHandler("بداية", handlers.start))
    
    # Error handler
    application.add_error_handler(handlers._send_error)
