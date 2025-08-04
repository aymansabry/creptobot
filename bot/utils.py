import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db_session, User
from config import Config
from messages import ARABIC_MESSAGES, get_message

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_inline_keyboard(buttons: Dict[str, str], columns: int = 2) -> InlineKeyboardMarkup:
    """
    إنشاء لوحة مفاتيح داخلية من قاموس الأزرار
    :param buttons: قاموس {text: callback_data}
    :param columns: عدد الأعمدة
    :return: كائن InlineKeyboardMarkup
    """
    keyboard = []
    row = []
    
    for idx, (text, callback_data) in enumerate(buttons.items(), start=1):
        row.append(InlineKeyboardButton(text, callback_data=callback_data))
        
        if idx % columns == 0 or idx == len(buttons):
            keyboard.append(row)
            row = []
    
    return InlineKeyboardMarkup(keyboard)

def create_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    إنشاء لوحة المفاتيح الرئيسية للقائمة
    """
    keyboard = [
        ["📊 عرض الفرص", "💼 محفظتي"],
        ["📈 استثمار مستمر", "📝 التقارير"],
        ["⚙️ الإعدادات", "🆘 المساعدة"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="اختر خيارًا...")

def format_currency(value: float, currency: str = "USDT") -> str:
    """
    تنسيق القيم المالية
    """
    return f"{value:,.2f} {currency}"

def format_date(date: datetime, lang: str = "ar") -> str:
    """
    تنسيق التاريخ حسب اللغة
    """
    if lang == "ar":
        return date.strftime("%d/%m/%Y %I:%M %p")
    return date.strftime("%Y-%m-%d %H:%M")

def calculate_profit(investment: float, profit_percent: float) -> Dict[str, float]:
    """
    حساب الأرباح والرسوم
    """
    gross_profit = investment * (profit_percent / 100)
    fee = gross_profit * (Config.BOT_FEE_PERCENT / 100)
    net_profit = gross_profit - fee
    
    return {
        "gross_profit": gross_profit,
        "fee": fee,
        "net_profit": net_profit,
        "total_return": investment + net_profit
    }

def get_user_language(user_id: int) -> str:
    """
    الحصول على لغة المستخدم من قاعدة البيانات
    """
    session = get_db_session()
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        return user.language if user else Config.DEFAULT_LANGUAGE
    except Exception as e:
        logger.error(f"Error getting user language: {e}")
        return Config.DEFAULT_LANGUAGE
    finally:
        session.close()

def validate_amount(amount_str: str, min_amount: float = Config.MIN_INVESTMENT) -> Optional[float]:
    """
    التحقق من صحة المبلغ المدخل
    """
    try:
        amount = float(amount_str)
        if amount >= min_amount:
            return amount
        return None
    except ValueError:
        return None

def generate_trade_details(trade_data: Dict[str, Any], lang: str = "ar") -> str:
    """
    إنشاء تفاصيل الصفقة بصيغة مقروءة
    """
    profit_info = calculate_profit(trade_data['amount'], trade_data['profit_percent'])
    
    return get_message('trade_details', lang).format(
        symbol=trade_data['symbol'],
        buy_price=format_currency(trade_data['buy_price']),
        sell_price=format_currency(trade_data['sell_price']),
        amount=format_currency(trade_data['amount']),
        profit_percent=trade_data['profit_percent'],
        gross_profit=format_currency(profit_info['gross_profit']),
        fee=format_currency(profit_info['fee']),
        net_profit=format_currency(profit_info['net_profit']),
        total_return=format_currency(profit_info['total_return'])
    )

def generate_report_message(report_data: Dict[str, Any], lang: str = "ar") -> str:
    """
    إنشاء رسالة التقرير
    """
    advice = get_advice_based_on_performance(report_data['success_rate'])
    
    return get_message('report_header', lang).format(
        start=report_data['start_date'],
        end=report_data['end_date']
    ) + get_message('report_content', lang).format(
        trades=report_data['total_trades'],
        invested=format_currency(report_data['total_invested']),
        profit=format_currency(report_data['total_profit']),
        rate=report_data['success_rate'],
        advice=advice
    )

def get_advice_based_on_performance(success_rate: float) -> str:
    """
    تقديم نصائح استثمارية حسب الأداء
    """
    if success_rate >= 0.8:
        return "أداء ممتاز! نوصي بزيادة مبلغ الاستثمار"
    elif success_rate >= 0.6:
        return "أداء جيد، استمر في استراتيجيتك الحالية"
    elif success_rate >= 0.4:
        return "أداء متوسط، نوصي بتنويع الاستثمارات"
    else:
        return "أداء أقل من المتوقع، نوصي بمراجعة استراتيجية الاستثمار"

def log_user_activity(user_id: int, action: str, details: str = ""):
    """
    تسجيل نشاط المستخدم
    """
    logger.info(f"User Activity | ID: {user_id} | Action: {action} | Details: {details}")

def error_handler(update: object, context: Any) -> None:
    """
    معالج الأخطاء العام للبوت
    """
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update and hasattr(update, 'effective_user'):
        user_id = update.effective_user.id
        lang = get_user_language(user_id)
        
        try:
            update.effective_message.reply_text(
                get_message('error_occurred', lang)
            )
        except Exception as e:
            logger.error(f"Error sending error message: {e}")
