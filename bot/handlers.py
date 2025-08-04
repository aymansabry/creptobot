from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)
from datetime import datetime, timedelta
import logging
from .database import User, Transaction, Trade, get_db_session
from .trading import TradingEngine
from .analysis import MarketAnalyzer
from .config import Config
from .messages import ARABIC_MESSAGES as MSG
import json

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize trading components
trading_engine = TradingEngine()
market_analyzer = MarketAnalyzer(trading_engine)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    session = get_db_session()
    
    try:
        # Register new user
        new_user = User(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            wallet_address='',
            language='ar'
        )
        session.add(new_user)
        session.commit()
        
        # Show main menu
        keyboard = [
            ["📊 عرض الفرص", "💼 محفظتي"],
            ["📈 الاستثمار المستمر", "📝 التقارير"],
            ["⚙️ الإعدادات", "🆘 المساعدة"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            MSG['welcome'],
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Start error: {e}")
        await update.message.reply_text(MSG['error'])
    finally:
        session.close()

async def show_opportunities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show investment opportunities"""
    try:
        opportunities = market_analyzer.get_top_opportunities()
        
        if not opportunities:
            await update.message.reply_text(MSG['no_opportunities'])
            return
            
        keyboard = []
        for idx, opp in enumerate(opportunities, 1):
            # Create button for each opportunity
            keyboard.append([
                InlineKeyboardButton(
                    f"الفرصة {idx} - ربح {opp['profit_percent']:.2f}%",
                    callback_data=f"opp_{idx}"
                )
            ])
            
            # Send opportunity details
            await update.message.reply_text(
                opp['description_ar'],
                parse_mode='Markdown'
            )
            
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            MSG['select_opportunity'],
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Opportunities error: {e}")
        await update.message.reply_text(MSG['error'])

async def handle_opportunity_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle opportunity selection"""
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data.startswith('opp_'):
            opp_idx = int(query.data.split('_')[1]) - 1
            context.user_data['selected_opp'] = opp_idx
            await query.edit_message_text(MSG['enter_amount'])
            
        elif query.data == 'back':
            await query.edit_message_text(MSG['back_to_main'])
            
    except Exception as e:
        logger.error(f"Selection error: {e}")
        await query.edit_message_text(MSG['error'])

async def handle_investment_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process investment amount"""
    try:
        amount = float(update.message.text)
        if amount < Config.MIN_INVESTMENT:
            await update.message.reply_text(
                MSG['min_investment'].format(amount=Config.MIN_INVESTMENT)
            )
            return
            
        opp_idx = context.user_data.get('selected_opp')
        opportunities = market_analyzer.get_top_opportunities()
        selected_opp = opportunities[opp_idx]
        
        # Execute trade
        trade_data = {
            'symbol': selected_opp['symbol'],
            'buy_price': selected_opp['buy_price'],
            'sell_price': selected_opp['sell_price'],
            'amount': amount,
            'profit_percent': selected_opp['profit_percent'],
            'user_id': update.effective_user.id
        }
        
        if trading_engine.execute_trade(trade_data):
            await update.message.reply_text(
                MSG['trade_success'].format(
                    amount=amount,
                    profit=amount * selected_opp['profit_percent'] / 100,
                    currency='USDT'
                )
            )
        else:
            await update.message.reply_text(MSG['trade_failed'])
            
    except ValueError:
        await update.message.reply_text(MSG['invalid_amount'])
    except Exception as e:
        logger.error(f"Investment error: {e}")
        await update.message.reply_text(MSG['error'])

def setup_handlers(application):
    """Register all handlers"""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_investment_amount))
    application.add_handler(CallbackQueryHandler(handle_opportunity_selection))
    
    # Arabic command handlers
    application.add_handler(CommandHandler("الفرص", show_opportunities))
    application.add_handler(CommandHandler("محفظتي", show_wallet_balance))
