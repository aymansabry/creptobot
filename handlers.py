# handlers.py
import telebot
import database
import utils
import ccxt
from telebot import types

bot = telebot.TeleBot(database.BOT_TOKEN)

# قائمة المستخدم
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    database.add_user(user_id)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 تسجيل أو تعديل بيانات التداول")
    markup.add("🚀 ابدأ استثمار", "🧪 استثمار وهمي")
    markup.add("📜 كشف حساب عن فترة")
    markup.add("📈 حالة السوق", "⛔ إيقاف الاستثمار")
    bot.send_message(user_id, "👋 أهلاً بك! اختر من القائمة:", reply_markup=markup)

# 1- تسجيل أو تعديل بيانات التداول
@bot.message_handler(func=lambda m: m.text == "📊 تسجيل أو تعديل بيانات التداول")
def register_exchange(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Binance", callback_data="set_exchange_binance"))
    markup.add(types.InlineKeyboardButton("KuCoin", callback_data="set_exchange_kucoin"))
    bot.send_message(message.chat.id, "📌 اختر المنصة:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_exchange_"))
def set_exchange(call):
    exchange_name = call.data.split("_")[2]
    msg = bot.send_message(call.message.chat.id, f"🔑 أرسل مفتاح API الخاص بـ {exchange_name}:")
    bot.register_next_step_handler(msg, lambda m: get_api_secret(m, exchange_name))

def get_api_secret(message, exchange_name):
    api_key = message.text
    msg = bot.send_message(message.chat.id, "🔐 أرسل مفتاح Secret:")
    bot.register_next_step_handler(msg, lambda m: save_exchange_data(m, exchange_name, api_key))

def save_exchange_data(message, exchange_name, api_key):
    api_secret = message.text
    user_id = message.from_user.id

    try:
        # اختبار الاتصال بالمنصة
        client = getattr(ccxt, exchange_name.lower())({
            "apiKey": api_key,
            "secret": api_secret
        })
        client.fetch_balance()

        # حفظ البيانات
        database.save_exchange(user_id, exchange_name.lower(), api_key, api_secret, sandbox=False)
        bot.send_message(user_id, "✅ تم حفظ بيانات المنصة بنجاح، وهي تعمل الآن.")
    except Exception as e:
        bot.send_message(user_id, f"❌ خطأ: {str(e)}\nأعد المحاولة.")

# 2- ابدأ استثمار
@bot.message_handler(func=lambda m: m.text == "🚀 ابدأ استثمار")
def start_investment(message):
    user_id = message.from_user.id
    msg = bot.send_message(user_id, "💵 أدخل مبلغ الاستثمار بالدولار:")
    bot.register_next_step_handler(msg, process_investment_amount)

def process_investment_amount(message):
    try:
        amount_usd = float(message.text)
        user_id = message.from_user.id
        utils.execute_investment(user_id, "BTC/USDT", amount_usd)
        bot.send_message(user_id, "✅ تم بدء الاستثمار الفعلي.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}")

# 3- استثمار وهمي
@bot.message_handler(func=lambda m: m.text == "🧪 استثمار وهمي")
def fake_investment(message):
    user_id = message.from_user.id
    try:
        utils.test_sandbox_order(user_id, "BTC/USDT", "buy", 0.001)
        bot.send_message(user_id, "🧪 تم تنفيذ استثمار وهمي (sandbox).")
    except Exception as e:
        bot.send_message(user_id, f"❌ خطأ: {str(e)}")

# 4- كشف حساب
@bot.message_handler(func=lambda m: m.text == "📜 كشف حساب عن فترة")
def account_statement(message):
    msg = bot.send_message(message.chat.id, "📅 أدخل تاريخ البداية (YYYY-MM-DD):")
    bot.register_next_step_handler(msg, get_end_date)

def get_end_date(message):
    start_date = message.text
    msg = bot.send_message(message.chat.id, "📅 أدخل تاريخ النهاية (YYYY-MM-DD):")
    bot.register_next_step_handler(msg, lambda m: send_statement(m, start_date))

def send_statement(message, start_date):
    end_date = message.text
    user_id = message.from_user.id
    data = database.get_statement(user_id, start_date, end_date)
    if data:
        bot.send_message(user_id, f"📊 كشف الحساب من {start_date} إلى {end_date}:\n{data}")
    else:
        bot.send_message(user_id, "📭 لا توجد بيانات.")

# 5- حالة السوق
@bot.message_handler(func=lambda m: m.text == "📈 حالة السوق")
def market_status(message):
    try:
        client = utils.get_exchange_client(message.from_user.id)
        ticker = client.fetch_ticker("BTC/USDT")
        bot.send_message(message.chat.id, f"💹 سعر BTC الآن: {ticker['last']} USDT")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}")

# 6- إيقاف الاستثمار
@bot.message_handler(func=lambda m: m.text == "⛔ إيقاف الاستثمار")
def stop_investment(message):
    user_id = message.from_user.id
    database.deactivate_user(user_id)
    bot.send_message(user_id, "⛔ تم إيقاف الاستثمار لهذا الحساب.")

print("✅ Handlers loaded")
