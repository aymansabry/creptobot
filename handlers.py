# handlers.py
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import mysql.connector
from database import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
import ccxt
import random
import time

# الاتصال بقاعدة البيانات
def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# القوائم
main_menu = ReplyKeyboardMarkup([
    ["💰 استثمار وهمي", "💵 استثمار حقيقي"],
    ["📊 حالة السوق", "⚙️ إدارة المنصات"]
], resize_keyboard=True)

def get_platforms(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM platforms WHERE user_id = %s", (user_id,))
    platforms = cursor.fetchall()
    conn.close()
    return platforms

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT IGNORE INTO users (telegram_id) VALUES (%s)", (user_id,))
    conn.commit()
    conn.close()

    await update.message.reply_text("👋 أهلاً بك! اختر من القائمة:", reply_markup=main_menu)

# الاستثمار الوهمي
async def virtual_investment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    platforms = get_platforms(user_id)

    if not platforms:
        await update.message.reply_text("⚠️ أضف منصات التداول أولاً من 'إدارة المنصات'")
        return

    await update.message.reply_text("💵 حدد المبلغ للاستثمار الوهمي (بالدولار):")
    context.user_data["invest_type"] = "virtual"

async def set_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ رجاءً أدخل رقم صحيح.")
        return

    context.user_data["amount"] = amount
    await update.message.reply_text(
        f"✅ تم تعيين المبلغ: {amount} دولار\n⏳ جاري تحديث بيانات السوق لاختيار فرصة مربحة..."
    )

    # محاكاة تحليل السوق
    time.sleep(2)
    symbol_buy = "BTC/USDT"
    symbol_sell = "ETH/USDT"

    await update.message.reply_text(f"📈 جاري شراء عملة {symbol_buy}...")
    time.sleep(2)
    await update.message.reply_text(f"📉 جاري بيع عملة {symbol_sell}...")

    # حساب الربح الوهمي
    profit = round(amount * random.uniform(0.01, 0.05), 2)

    await update.message.reply_text(
        f"✅ تمت العملية بنجاح!\n💵 أرباحك هي {profit} دولار بعد خصم نسبة البوت.\n"
        f"💡 لو استثمرت معانا فعلياً كنت هتكسب نفس النسبة تقريباً."
    )

# عرض حالة السوق
async def market_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 جاري تحليل السوق...")
    time.sleep(2)

    analysis = (
        "السوق في حالة استقرار نسبي اليوم.\n"
        "BTC حول 29000$\nETH حول 1850$\n"
        "قد نرى تحرك صعودي خلال الساعات القادمة."
    )

    await update.message.reply_text(analysis)

