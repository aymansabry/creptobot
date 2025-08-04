from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from database import User, Transaction, Trade, Report, get_db_session
from trading import TradingEngine
from analysis import MarketAnalyzer
from messages import ARABIC_MESSAGES
from datetime import datetime, timedelta
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

trading_engine = TradingEngine()
market_analyzer = MarketAnalyzer(trading_engine)

# نظام القوائم الرئيسية بالأزرار
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📊 عرض الفرص الاستثمارية", "💼 محفظتي"],
        ["📈 الاستثمار المستمر", "📝 تقارير الاستثمار"],
        ["⚙️ الإعدادات", "🆘 المساعدة"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        ARABIC_MESSAGES['main_menu'],
        reply_markup=reply_markup
    )

# معالج الأزرار الرئيسية
async def handle_main_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "📊 عرض الفرص الاستثمارية":
        await show_investment_opportunities(update, context)
    elif text == "💼 محفظتي":
        await show_wallet(update, context)
    elif text == "📈 الاستثمار المستمر":
        await show_continuous_investment(update, context)
    elif text == "📝 تقارير الاستثمار":
        await ask_for_report_period(update, context)
    elif text == "⚙️ الإعدادات":
        await show_settings(update, context)
    elif text == "🆘 المساعدة":
        await show_help(update, context)

# عرض الفرص الاستثمارية مع أزرار
async def show_investment_opportunities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    opportunities = market_analyzer.get_top_opportunities()
    
    if not opportunities:
        await update.message.reply_text(ARABIC_MESSAGES['no_opportunities'])
        return
    
    message = ARABIC_MESSAGES['opportunities_header']
    keyboard = []
    
    for idx, opp in enumerate(opportunities[:5], start=1):
        message += ARABIC_MESSAGES['opportunity_item'].format(
            index=idx,
            description=opp['description'],
            profit=opp['profit_percent']
        )
        
        keyboard.append([InlineKeyboardButton(
            f"استثمر في الفرصة #{idx}",
            callback_data=f"invest_{idx}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back_to_main')])
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# نظام التقارير
async def ask_for_report_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("آخر 7 أيام", callback_data='report_7')],
        [InlineKeyboardButton("آخر 30 يومًا", callback_data='report_30')],
        [InlineKeyboardButton("اختيار فترة مخصصة", callback_data='report_custom')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_main')]
    ]
    
    await update.message.reply_text(
        ARABIC_MESSAGES['report_period_prompt'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE, days: int = None):
    user_id = update.effective_user.id
    session = get_db_session()
    
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days) if days else context.user_data.get('report_start')
        
        # جلب البيانات من قاعدة البيانات
        trades = session.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.timestamp >= start_date,
            Trade.timestamp <= end_date,
            Trade.status == 'completed'
        ).all()
        
        total_invested = sum(trade.amount for trade in trades)
        total_profit = sum(trade.profit for trade in trades)
        success_rate = len([t for t in trades if t.profit > 0]) / len(trades) if trades else 0
        
        report_data = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'total_trades': len(trades),
            'total_invested': total_invested,
            'total_profit': total_profit,
            'success_rate': f"{success_rate:.2%}",
            'most_profitable': max(trades, key=lambda x: x.profit).metadata if trades else None
        }
        
        # حفظ التقرير في قاعدة البيانات
        report = Report(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            report_data=json.dumps(report_data)
        )
        session.add(report)
        session.commit()
        
        # إرسال التقرير للمستخدم
        await send_report_to_user(update, report_data)
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        await update.callback_query.message.reply_text(ARABIC_MESSAGES['report_error'])
    finally:
        session.close()

async def send_report_to_user(update: Update, report_data: dict):
    message = ARABIC_MESSAGES['report_header'].format(
        start=report_data['start_date'],
        end=report_data['end_date']
    )
    
    message += ARABIC_MESSAGES['report_content'].format(
        trades=report_data['total_trades'],
        invested=report_data['total_invested'],
        profit=report_data['total_profit'],
        rate=report_data['success_rate']
    )
    
    await update.callback_query.message.reply_text(message)
