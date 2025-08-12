from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_db_connection
import ccxt
import random
import time

# ==================================================
# حفظ المبلغ
# ==================================================
async def set_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        user_id = update.effective_user.id

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET amount=%s WHERE telegram_id=%s", (amount, user_id))
        conn.commit()
        cursor.close()
        conn.close()

        await update.message.reply_text(f"💰 تم تعيين المبلغ: {amount} دولار\nاختر نوع الاستثمار:")
        keyboard = [
            [InlineKeyboardButton("💹 استثمار وهمي", callback_data="virtual_invest")],
            [InlineKeyboardButton("💵 استثمار حقيقي", callback_data="real_invest")]
        ]
        await update.message.reply_text("اختر:", reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        await update.message.reply_text("❌ صيغة الأمر غير صحيحة. مثال:\n/set_amount 100")

# ==================================================
# تنفيذ الاستثمار (مشترك للوهمي والحقيقي)
# ==================================================
async def execute_investment(update: Update, context: ContextTypes.DEFAULT_TYPE, is_real=False):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE telegram_id=%s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user or not user.get("amount"):
        await query.edit_message_text("⚠️ برجاء تحديد المبلغ أولاً باستخدام /set_amount")
        return

    # 🔹 الخطوة 1: تحديد المبلغ
    amount = float(user["amount"])
    msg = f"💰 المبلغ المحدد: {amount} دولار\n"
    msg += "⚠️ الاستثمار بدون أموال حقيقية" if not is_real else "✅ استثمار بأموال حقيقية"
    await query.edit_message_text(msg)
    time.sleep(1)

    # 🔹 الخطوة 2: مراجعة المنصات
    platforms = []
    if user.get("binance_api_key") and user.get("binance_api_secret"):
        platforms.append("Binance")
    if user.get("kucoin_api_key") and user.get("kucoin_api_secret") and user.get("kucoin_passphrase"):
        platforms.append("KuCoin")

    if not platforms:
        await query.message.reply_text("⚠️ لم يتم إضافة أي منصات. برجاء إضافتها أولاً.")
        return

    await query.message.reply_text(f"🔍 جاري التحقق من المنصات: {', '.join(platforms)}")
    time.sleep(1)

    # 🔹 الخطوة 3: تحديث بيانات السوق
    await query.message.reply_text("📈 جاري تحديث بيانات السوق لاختيار فرصة مربحة...")
    time.sleep(2)

    # 🔹 الخطوة 4: اختيار عملة عشوائية (محاكاة)
    coins = ["BTC/USDT", "ETH/USDT", "ADA/USDT", "XRP/USDT"]
    coin = random.choice(coins)
    buy_price = round(random.uniform(100, 30000), 2)

    await query.message.reply_text(f"🛒 جاري شراء {coin} بسعر {buy_price} USDT")
    time.sleep(1)

    # 🔹 الخطوة 5: بيع العملة
    sell_price = round(buy_price * random.uniform(1.01, 1.05), 2)
    await query.message.reply_text(f"💰 جاري بيع {coin} بسعر {sell_price} USDT")
    time.sleep(1)

    # 🔹 حساب الربح
    profit = round((sell_price - buy_price) * (amount / buy_price), 2)
    bot_fee = round(profit * 0.05, 2)
    net_profit = profit - bot_fee

    await query.message.reply_text(
        f"✅ تمت العملية بنجاح!\n"
        f"📊 أرباحك: {net_profit} دولار بعد خصم نسبة البوت (5%)"
    )

# ==================================================
# استثمار وهمي
# ==================================================
async def virtual_invest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await execute_investment(update, context, is_real=False)

# ==================================================
# استثمار حقيقي
# ==================================================
async def real_invest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await execute_investment(update, context, is_real=True)
