import logging
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import ccxt
import openai
from database import get_connection, create_tables
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=5)

# User states
(
    STATE_NONE,
    STATE_BINANCE_API,
    STATE_BINANCE_SECRET,
    STATE_KUCOIN_API,
    STATE_KUCOIN_SECRET,
    STATE_KUCOIN_PASSWORD,
    STATE_INVEST_AMOUNT,
    STATE_SELECT_DATE_FOR_FAKE_INVEST,
    STATE_SELECT_REPORT_START_DATE,
    STATE_SELECT_REPORT_END_DATE,
    STATE_ADMIN_AUTH,
    STATE_ADMIN_MAIN,
    STATE_ADMIN_EDIT_PROFIT_PERCENT,
) = range(13)

user_states = {}
user_context = {}  # Temporary context per user for dates etc.

# Helper for async ccxt calls
async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args))


# Database helper functions

def set_user_platform_api(user_id, platform, api_key=None, secret=None, password=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT active_platforms FROM users WHERE telegram_id=%s", (user_id,))
    row = cursor.fetchone()
    active_platforms = {}
    if row and row[0]:
        import json
        active_platforms = json.loads(row[0])
    if platform not in active_platforms:
        active_platforms[platform] = {}

    if api_key:
        active_platforms[platform]["apiKey"] = api_key
    if secret:
        active_platforms[platform]["secret"] = secret
    if password:
        active_platforms[platform]["password"] = password

    active_platforms_json = json.dumps(active_platforms)

    cursor.execute(
        """
        INSERT INTO users (telegram_id, active_platforms)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE active_platforms=%s
        """,
        (user_id, active_platforms_json, active_platforms_json),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_user_active_platforms(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT active_platforms FROM users WHERE telegram_id=%s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    import json
    if row and row[0]:
        return json.loads(row[0])
    return {}


def set_user_invest_amount(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET invested_amount=%s WHERE telegram_id=%s", (amount, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_user_invest_amount(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT invested_amount FROM users WHERE telegram_id=%s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else 0


def set_user_investing_status(user_id, status: bool):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_investing=%s WHERE telegram_id=%s", (status, user_id))
    conn.commit()
    cursor.close()
    conn.close()


def get_user_profit(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT profit FROM users WHERE telegram_id=%s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else 0


def get_owner_profit_percentage():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT profit_percentage FROM owner_wallet WHERE id=1")
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else 10.0


def set_owner_profit_percentage(percent: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO owner_wallet (id, profit_percentage) VALUES (1, %s) ON DUPLICATE KEY UPDATE profit_percentage=%s",
        (percent, percent),
    )
    conn.commit()
    cursor.close()
    conn.close()


def log_investment(
    telegram_id, platform, operation, amount, price,
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO investment_history (telegram_id, platform, operation, amount, price)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (telegram_id, platform, operation, amount, price),
    )
    conn.commit()
    cursor.close()
    conn.close()


# OpenAI integration
async def openai_market_analysis(prices_summary: str) -> str:
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "أنت خبير في تحليل أسواق العملات الرقمية وتقديم نصائح تداول عملية."
                },
                {"role": "user", "content": prices_summary},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return "عذراً، لم أتمكن من جلب تحليل السوق حالياً."


# UI helpers
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("1️⃣ تسجيل أو تعديل بيانات التداول", callback_data="menu_trading_data")],
        [InlineKeyboardButton("2️⃣ ابدأ استثمار", callback_data="menu_start_invest")],
        [InlineKeyboardButton("3️⃣ استثمار وهمي", callback_data="menu_fake_invest")],
        [InlineKeyboardButton("4️⃣ كشف حساب عن فترة", callback_data="menu_report")],
        [InlineKeyboardButton("5️⃣ حالة السوق", callback_data="menu_market_status")],
        [InlineKeyboardButton("6️⃣ إيقاف الاستثمار", callback_data="menu_stop_invest")],
        [InlineKeyboardButton("🔧 قائمة المدير", callback_data="menu_admin")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_main_keyboard():
    keyboard = [[InlineKeyboardButton("⬅️ رجوع للقائمة الرئيسية", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)


# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك في بوت الاستثمار، اختر من القائمة:",
        reply_markup=main_menu_keyboard(),
    )


# Callback query handler
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "main_menu":
        await query.message.edit_text(
            "القائمة الرئيسية:", reply_markup=main_menu_keyboard()
        )
        user_states[user_id] = STATE_NONE
        return

    if query.data == "menu_trading_data":
        user_states[user_id] = STATE_BINANCE_API
        await query.message.edit_text(
            "أدخل Binance API Key أو اضغط رجوع:",
            reply_markup=back_to_main_keyboard(),
        )
        return

    if query.data == "menu_start_invest":
        await query.message.edit_text(
            "🔔 بدء الاستثمار الحقيقي جارٍ... (سيتم تنفيذ الخوارزميات لاحقاً)",
            reply_markup=back_to_main_keyboard(),
        )
        set_user_investing_status(user_id, True)
        return

    if query.data == "menu_fake_invest":
        user_states[user_id] = STATE_SELECT_DATE_FOR_FAKE_INVEST
        await query.message.edit_text(
            "الرجاء إدخال تاريخ لبدء الاستثمار الوهمي (YYYY-MM-DD):",
            reply_markup=back_to_main_keyboard(),
        )
        return

    if query.data == "menu_report":
        user_states[user_id] = STATE_SELECT_REPORT_START_DATE
        await query.message.edit_text(
            "الرجاء إدخال تاريخ بداية الفترة (YYYY-MM-DD):",
            reply_markup=back_to_main_keyboard(),
        )
        return

    if query.data == "menu_market_status":
        await query.message.edit_text(
            "جاري جلب حالة السوق اللحظية مع التحليل..."
        )
        summary = await get_market_status_analysis()
        await query.message.edit_text(
            f"📊 حالة السوق اللحظية:\n\n{summary}",
            reply_markup=main_menu_keyboard(),
        )
        return

    if query.data == "menu_stop_invest":
        set_user_investing_status(user_id, False)
        await query.message.edit_text(
            "تم إيقاف الاستثمار الخاص بك، لن يتم استخدام أموالك في الصفقات حتى تقوم بالتفعيل مرة أخرى.",
            reply_markup=main_menu_keyboard(),
        )
        return

    if query.data == "menu_admin":
        ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
        if user_id != ADMIN_TELEGRAM_ID:
            await query.message.edit_text(
                "🚫 أنت لست مديراً، لا يمكنك الدخول لهذه القائمة.",
                reply_markup=main_menu_keyboard(),
            )
            return
        user_states[user_id] = STATE_ADMIN_MAIN
        await query.message.edit_text(
            "⚙️ قائمة المدير:",
            reply_markup=admin_main_menu_keyboard(),
        )
        return

    if user_states.get(user_id) == STATE_ADMIN_MAIN:
        if query.data == "admin_edit_profit_percent":
            user_states[user_id] = STATE_ADMIN_EDIT_PROFIT_PERCENT
            await query.message.edit_text(
                "أدخل نسبة ربح البوت الجديدة (مثل 10 لـ 10%):",
                reply_markup=back_to_main_keyboard(),
            )
            return
        if query.data == "admin_view_stats":
            count = get_total_users_count()
            online_count = get_online_users_count()
            await query.message.edit_text(
                f"📈 الإحصائيات:\nعدد المستخدمين الكلي: {count}\nالمستخدمين النشطين: {online_count}",
                reply_markup=admin_main_menu_keyboard(),
            )
            return
        if query.data == "admin_back_to_main":
            user_states[user_id] = STATE_ADMIN_MAIN
            await query.message.edit_text(
                "⚙️ قائمة المدير:",
                reply_markup=admin_main_menu_keyboard(),
            )
            return


async def get_market_status_analysis():
    try:
        exchange = ccxt.binance()
        tickers = await run_in_executor(exchange.fetch_tickers)
        summary = "العملات الرئيسية وأسعارها الحالية:\n"
        top_coins = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT"]
        for coin in top_coins:
            if coin in tickers:
                price = tickers[coin]["last"]
                summary += f"{coin}: {price}$\n"
        analysis = await openai_market_analysis(summary)
        return analysis
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        return "عذراً، لا يمكن جلب بيانات السوق حالياً."


def admin_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("تعديل نسبة ربح البوت", callback_data="admin_edit_profit_percent")],
        [InlineKeyboardButton("عرض إحصائيات المستخدمين", callback_data="admin_view_stats")],
        [InlineKeyboardButton("رجوع للقائمة الرئيسية", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_total_users_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count


def get_online_users_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_investing=TRUE")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count


# Message handler for text inputs
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    state = user_states.get(user_id, STATE_NONE)

    if text == "⬅️ رجوع للقائمة الرئيسية":
        await update.message.reply_text(
            "القائمة الرئيسية:", reply_markup=main_menu_keyboard()
        )
        user_states[user_id] = STATE_NONE
        return

    if state == STATE_BINANCE_API:
        set_user_platform_api(user_id, "binance", api_key=text)
        user_states[user_id] = STATE_BINANCE_SECRET
        await update.message.reply_text(
            "أدخل Binance Secret Key أو اضغط رجوع:", reply_markup=back_to_main_keyboard()
        )
    elif state == STATE_BINANCE_SECRET:
        set_user_platform_api(user_id, "binance", secret=text)
        user_states[user_id] = STATE_KUCOIN_API
        await update.message.reply_text(
            "أدخل KuCoin API Key مع تعليمات الحصول عليه أو اضغط رجوع:\nhttps://docs.kucoin.com/",
            reply_markup=back_to_main_keyboard(),
        )
    elif state == STATE_KUCOIN_API:
        set_user_platform_api(user_id, "kucoin", api_key=text)
        user_states[user_id] = STATE_KUCOIN_SECRET
        await update.message.reply_text(
            "أدخل KuCoin Secret Key أو اضغط رجوع:", reply_markup=back_to_main_keyboard()
        )
    elif state == STATE_KUCOIN_SECRET:
        set_user_platform_api(user_id, "kucoin", secret=text)
        user_states[user_id] = STATE_KUCOIN_PASSWORD
        await update.message.reply_text(
            "أدخل KuCoin API Password (Passphrase) أو اضغط رجوع:", reply_markup=back_to_main_keyboard()
        )
    elif state == STATE_KUCOIN_PASSWORD:
        set_user_platform_api(user_id, "kucoin", password=text)
        user_states[user_id] = STATE_INVEST_AMOUNT
        await update.message.reply_text(
            "أدخل مبلغ الاستثمار (رقم فقط) أو اضغط رجوع:", reply_markup=back_to_main_keyboard()
        )
    elif state == STATE_INVEST_AMOUNT:
        if text.replace('.', '', 1).isdigit():
            amount = float(text)
            set_user_invest_amount(user_id, amount)
            user_states[user_id] = STATE_NONE
            await update.message.reply_text(
                f"تم تعيين مبلغ الاستثمار: {amount} دولار", reply_markup=main_menu_keyboard()
            )
        else:
            await update.message.reply_text("الرجاء إدخال رقم صالح.")
    elif state == STATE_SELECT_DATE_FOR_FAKE_INVEST:
        # هنا من المفترض التأكد من صحة التاريخ (YYYY-MM-DD)
        try:
            import datetime
            datetime.datetime.strptime(text, "%Y-%m-%d")
            user_context[user_id] = {"fake_invest_date": text}
            user_states[user_id] = STATE_NONE
            # تنفذ هنا الاستثمارات الوهمية باستخدام البيانات المؤرشفة لهذا التاريخ
            await update.message.reply_text(
                f"تم تعيين تاريخ الاستثمار الوهمي: {text}\nيتم المحاكاة... (قيد التطوير)",
                reply_markup=main_menu_keyboard(),
            )
        except ValueError:
            await update.message.reply_text(
                "التاريخ غير صالح، الرجاء إدخال التاريخ بصيغة YYYY-MM-DD"
            )
    elif state == STATE_SELECT_REPORT_START_DATE:
        try:
            import datetime
            datetime.datetime.strptime(text, "%Y-%m-%d")
            user_context[user_id] = {"report_start_date": text}
            user_states[user_id] = STATE_SELECT_REPORT_END_DATE
            await update.message.reply_text(
                "الرجاء إدخال تاريخ نهاية الفترة (YYYY-MM-DD):",
                reply_markup=back_to_main_keyboard(),
            )
        except ValueError:
            await update.message.reply_text(
                "التاريخ غير صالح، الرجاء إدخال التاريخ بصيغة YYYY-MM-DD"
            )
    elif state == STATE_SELECT_REPORT_END_DATE:
        try:
            import datetime
            datetime.datetime.strptime(text, "%Y-%m-%d")
            start_date = user_context[user_id].get("report_start_date")
            end_date = text
            user_states[user_id] = STATE_NONE
            # تنفيذ جلب تقرير بين التواريخ
            # (قيد التطوير)
            await update.message.reply_text(
                f"يتم الآن جلب كشف الحساب من {start_date} إلى {end_date}... (قيد التطوير)",
                reply_markup=main_menu_keyboard(),
            )
        except ValueError:
            await update.message.reply_text(
                "التاريخ غير صالح، الرجاء إدخال التاريخ بصيغة YYYY-MM-DD"
            )
    elif state == STATE_ADMIN_EDIT_PROFIT_PERCENT:
        try:
            percent = float(text)
            if 0 <= percent <= 100:
                set_owner_profit_percentage(percent)
                user_states[user_id] = STATE_ADMIN_MAIN
                await update.message.reply_text(
                    f"تم تعديل نسبة ربح البوت إلى {percent}%",
                    reply_markup=admin_main_menu_keyboard(),
                )
            else:
                await update.message.reply_text("الرجاء إدخال رقم بين 0 و 100.")
        except ValueError:
            await update.message.reply_text("الرجاء إدخال رقم صالح.")
    else:
        await update.message.reply_text(
            "الرجاء اختيار خيار من القائمة أو استخدام الأزرار.",
            reply_markup=main_menu_keyboard(),
        )


def main():
    create_tables()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()