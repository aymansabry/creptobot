# handlers.py
import telebot
import database
import utils
import market_analysis

BOT_TOKEN = database.get_setting("bot_token", "")
bot = telebot.TeleBot(BOT_TOKEN)

# ==========================
# القوائم الرئيسية للمستخدم
# ==========================
@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 تسجيل أو تعديل بيانات التداول", "💰 محفظة المستخدم")
    markup.add("🚀 ابدأ استثمار", "🧪 استثمار وهمي")
    markup.add("📄 كشف حساب", "📈 حالة السوق")
    markup.add("⛔ إيقاف الاستثمار")
    bot.send_message(message.chat.id, "👋 أهلاً بك! اختر من القائمة:", reply_markup=markup)

# ==========================
# تسجيل أو تعديل بيانات التداول
# ==========================
@bot.message_handler(func=lambda m: m.text == "📊 تسجيل أو تعديل بيانات التداول")
def register_api(message):
    bot.send_message(message.chat.id, "📌 اختر المنصة (Binance / KuCoin / Bybit):")
    bot.register_next_step_handler(message, get_platform)

def get_platform(message):
    platform = message.text.strip().lower()
    bot.send_message(message.chat.id, f"🔑 أدخل API Key الخاصة بـ {platform}:")
    bot.register_next_step_handler(message, lambda m: get_api_key(m, platform))

def get_api_key(message, platform):
    api_key = message.text.strip()
    bot.send_message(message.chat.id, "🔐 أدخل API Secret:")
    bot.register_next_step_handler(message, lambda m: save_api_keys(m, platform, api_key))

def save_api_keys(message, platform, api_key):
    api_secret = message.text.strip()
    try:
        exchange = utils.get_exchange(platform, api_key, api_secret)
        exchange.load_markets()  # التحقق من صحة الاتصال
        database.save_api_key(message.chat.id, platform, api_key, api_secret)
        bot.send_message(message.chat.id, "✅ تم حفظ مفاتيح API بنجاح (اتصال صحيح).")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ في الاتصال: {e}")

# ==========================
# بدء الاستثمار
# ==========================
@bot.message_handler(func=lambda m: m.text == "🚀 ابدأ استثمار")
def start_investment(message):
    bot.send_message(message.chat.id, "💲 أدخل زوج العملة (مثل BTC/USDT):")
    bot.register_next_step_handler(message, get_symbol_for_trade)

def get_symbol_for_trade(message):
    symbol = message.text.upper()
    bot.send_message(message.chat.id, "📈 أدخل الكمية:")
    bot.register_next_step_handler(message, lambda m: execute_real_trade(m, symbol))

def execute_real_trade(message, symbol):
    try:
        amount = float(message.text)
        result = utils.execute_trade(message.chat.id, "binance", symbol, "buy", amount)
        bot.send_message(message.chat.id, f"✅ تم التنفيذ: {result}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {e}")

# ==========================
# استثمار وهمي
# ==========================
@bot.message_handler(func=lambda m: m.text == "🧪 استثمار وهمي")
def start_virtual(message):
    bot.send_message(message.chat.id, "💲 أدخل زوج العملة (مثل BTC/USDT):")
    bot.register_next_step_handler(message, get_symbol_for_virtual)

def get_symbol_for_virtual(message):
    symbol = message.text.upper()
    bot.send_message(message.chat.id, "📈 أدخل الكمية:")
    bot.register_next_step_handler(message, lambda m: execute_virtual_trade(m, symbol))

def execute_virtual_trade(message, symbol):
    try:
        amount = float(message.text)
        database.set_sandbox_mode(True)
        result = utils.execute_trade(message.chat.id, "binance", symbol, "buy", amount)
        bot.send_message(message.chat.id, f"💡 تنفيذ وهمي: {result}")
        database.set_sandbox_mode(False)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {e}")

# ==========================
# حالة السوق
# ==========================
@bot.message_handler(func=lambda m: m.text == "📈 حالة السوق")
def market_status(message):
    analysis = market_analysis.get_market_summary()
    bot.send_message(message.chat.id, analysis)

# ==========================
# كشف حساب
# ==========================
@bot.message_handler(func=lambda m: m.text == "📄 كشف حساب")
def account_statement(message):
    bot.send_message(message.chat.id, "📅 أدخل تاريخ البداية (YYYY-MM-DD):")
    bot.register_next_step_handler(message, get_start_date)

def get_start_date(message):
    start_date = message.text.strip()
    bot.send_message(message.chat.id, "📅 أدخل تاريخ النهاية (YYYY-MM-DD):")
    bot.register_next_step_handler(message, lambda m: show_statement(m, start_date))

def show_statement(message, start_date):
    end_date = message.text.strip()
    report = database.get_trades_report(message.chat.id, start_date, end_date)
    bot.send_message(message.chat.id, f"📊 تقرير الصفقات:\n{report}")

# ==========================
# إيقاف الاستثمار
# ==========================
@bot.message_handler(func=lambda m: m.text == "⛔ إيقاف الاستثمار")
def stop_investment(message):
    database.stop_user_investment(message.chat.id)
    bot.send_message(message.chat.id, "⛔ تم إيقاف الاستثمار لهذا الحساب.")

# ==========================
# تشغيل البوت
# ==========================
def run():
    print("🚀 البوت يعمل الآن...")
    bot.infinity_polling()
