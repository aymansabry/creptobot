# handlers.py
import telebot
from database import (
    get_user,
    save_user,
    update_user_setting,
    get_setting,
    get_all_users,
    save_trade,
    get_trades_by_period
)
from utils import (
    get_exchange,
    validate_api_key,
    execute_market_order,
    calculate_profit_with_fee,
    log_message
)

BOT_TOKEN = get_setting("telegram_bot_token", "")
bot = telebot.TeleBot(BOT_TOKEN)

# =========================
# قوائم المستخدم
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    user = get_user(message.from_user.id)
    if not user:
        save_user(message.from_user.id, "client")
    bot.send_message(message.chat.id, "👋 أهلاً بك في بوت الاستثمار. اختر من القائمة:")
    show_main_menu(message.chat.id)

def show_main_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📌 تسجيل أو تعديل بيانات التداول")
    markup.row("🚀 ابدأ استثمار", "🎯 استثمار وهمي")
    markup.row("📊 كشف حساب عن فترة", "📈 حالة السوق")
    markup.row("⛔ إيقاف الاستثمار")
    bot.send_message(chat_id, "📍 القائمة الرئيسية:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📌 تسجيل أو تعديل بيانات التداول")
def register_trading_data(message):
    bot.send_message(message.chat.id, "📍 اختر المنصة (مثال: binance أو kucoin):")
    bot.register_next_step_handler(message, process_exchange_name)

def process_exchange_name(message):
    update_user_setting(message.from_user.id, "exchange_name", message.text.strip().lower())
    bot.send_message(message.chat.id, "🔑 أدخل API Key:")
    bot.register_next_step_handler(message, process_api_key)

def process_api_key(message):
    update_user_setting(message.from_user.id, "api_key", message.text.strip())
    bot.send_message(message.chat.id, "🔒 أدخل API Secret:")
    bot.register_next_step_handler(message, process_api_secret)

def process_api_secret(message):
    update_user_setting(message.from_user.id, "api_secret", message.text.strip())
    bot.send_message(message.chat.id, "✅ جاري التحقق من المفاتيح...")
    user = get_user(message.from_user.id)
    if validate_api_key(user['exchange_name'], user['api_key'], user['api_secret']):
        bot.send_message(message.chat.id, "✅ المفاتيح صحيحة وتم تفعيل الحساب.")
    else:
        bot.send_message(message.chat.id, "❌ المفاتيح غير صحيحة. حاول مرة أخرى.")
        return
    bot.send_message(message.chat.id, "💰 أدخل مبلغ الاستثمار:")
    bot.register_next_step_handler(message, process_investment_amount)

def process_investment_amount(message):
    try:
        amount = float(message.text.strip())
        update_user_setting(message.from_user.id, "investment_amount", str(amount))
        bot.send_message(message.chat.id, "✅ تم حفظ مبلغ الاستثمار.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ المبلغ غير صالح.")

# =========================
# تشغيل الاستثمار
# =========================
@bot.message_handler(func=lambda m: m.text == "🚀 ابدأ استثمار")
def start_real_investment(message):
    user = get_user(message.from_user.id)
    if not user or not user['api_key']:
        bot.send_message(message.chat.id, "❌ لم تقم بإعداد بيانات التداول.")
        return
    try:
        exchange = get_exchange(user['exchange_name'], user['api_key'], user['api_secret'])
        order = execute_market_order(exchange, "BTC/USDT", "buy", float(user['investment_amount']))
        net_profit = calculate_profit_with_fee(50.0)
        save_trade(user['id'], user['exchange_name'], "BTC/USDT", "buy", order['price'], float(user['investment_amount']), net_profit)
        bot.send_message(message.chat.id, f"✅ تم تنفيذ الصفقة. الربح الصافي: {net_profit}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ أثناء التنفيذ: {e}")

@bot.message_handler(func=lambda m: m.text == "🎯 استثمار وهمي")
def start_fake_investment(message):
    bot.send_message(message.chat.id, "📊 تنفيذ استثمار وهمي...")
    net_profit = calculate_profit_with_fee(25.0)
    bot.send_message(message.chat.id, f"💰 ربح وهمي صافي: {net_profit}")

# =========================
# كشف حساب
# =========================
@bot.message_handler(func=lambda m: m.text == "📊 كشف حساب عن فترة")
def account_statement(message):
    bot.send_message(message.chat.id, "📅 أدخل تاريخ البداية بصيغة YYYY-MM-DD:")
    bot.register_next_step_handler(message, process_start_date)

def process_start_date(message):
    start_date = message.text.strip()
    bot.send_message(message.chat.id, "📅 أدخل تاريخ النهاية بصيغة YYYY-MM-DD:")
    bot.register_next_step_handler(message, lambda m: process_end_date(m, start_date))

def process_end_date(message, start_date):
    end_date = message.text.strip()
    trades = get_trades_by_period(message.from_user.id, start_date, end_date)
    if not trades:
        bot.send_message(message.chat.id, "❌ لا توجد صفقات في هذه الفترة.")
        return
    report = "\n".join([f"{t['symbol']} - {t['side']} - {t['profit']}" for t in trades])
    bot.send_message(message.chat.id, f"📊 كشف الحساب:\n{report}")

# =========================
# إيقاف الاستثمار
# =========================
@bot.message_handler(func=lambda m: m.text == "⛔ إيقاف الاستثمار")
def stop_investment(message):
    update_user_setting(message.from_user.id, "active", "false")
    bot.send_message(message.chat.id, "🛑 تم إيقاف الاستثمار لهذا الحساب.")

# =========================
# تشغيل البوت
# =========================
def run_bot():
    log_message("🤖 Bot is running...")
    bot.infinity_polling()

if __name__ == "__main__":
    run_bot()
