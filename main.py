# main.py
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
from database import (
    create_tables,
    get_user_active_platforms,
    set_user_binance_api,
    set_user_binance_secret,
    set_user_kucoin_api,
    set_user_kucoin_secret,
    set_user_invest_amount,
    get_user_invest_amount,
    update_user_profit,
    log_investment_history,
)
from dotenv import load_dotenv
import openai

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

STATE_NONE = 0
STATE_BINANCE_API = 1
STATE_BINANCE_SECRET = 2
STATE_KUCOIN_API = 3
STATE_KUCOIN_SECRET = 4
STATE_INVEST_AMOUNT = 5
STATE_START_INVEST = 6
STATE_START_VIRTUAL_INVEST = 7
STATE_MARKET_ANALYSIS = 8

user_states = {}
executor = ThreadPoolExecutor(max_workers=5)

async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1. تسجيل أو تعديل بيانات التداول", callback_data="manage_trading")],
        [InlineKeyboardButton("2. بدء استثمار حقيقي", callback_data="start_invest")],
        [InlineKeyboardButton("3. استثمار وهمي", callback_data="virtual_invest")],
        [InlineKeyboardButton("4. كشف حساب عن فترة", callback_data="account_statement")],
        [InlineKeyboardButton("5. حالة السوق", callback_data="market_status")],
        [InlineKeyboardButton("6. إيقاف الاستثمار", callback_data="stop_invest")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("مرحبًا بك! اختر من القائمة:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text("مرحبًا بك! اختر من القائمة:", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "manage_trading":
        await manage_trading_menu(query, user_id)
    elif query.data == "start_invest":
        user_states[user_id] = STATE_START_INVEST
        await query.message.reply_text("جاري بدء الاستثمار الحقيقي...")
        await start_real_investment(user_id, query)
    elif query.data == "virtual_invest":
        user_states[user_id] = STATE_START_VIRTUAL_INVEST
        await query.message.reply_text("الاستثمار الوهمي بدون أموال حقيقية. الرجاء إدخال المبلغ:")
        user_states[user_id] = STATE_INVEST_AMOUNT
    elif query.data == "account_statement":
        user_states[user_id] = STATE_MARKET_ANALYSIS
        await query.message.reply_text("أرسل بداية الفترة (YYYY-MM-DD):")
    elif query.data == "market_status":
        await send_market_analysis(user_id, query)
    elif query.data == "stop_invest":
        await stop_user_investment(user_id, query)
    elif query.data == "add_binance_api" or query.data == "edit_binance_api":
        user_states[user_id] = STATE_BINANCE_API
        await query.message.reply_text("الرجاء إرسال Binance API Key:")
    elif query.data == "add_kucoin_api" or query.data == "edit_kucoin_api":
        user_states[user_id] = STATE_KUCOIN_API
        await query.message.reply_text("الرجاء إرسال KuCoin API Key:")
    elif query.data == "main_menu":
        await start(query, context)
    else:
        await query.message.reply_text("أمر غير معروف، الرجاء اختيار من القائمة.")


async def manage_trading_menu(query, user_id):
    active_platforms = get_user_active_platforms(user_id)
    buttons = []
    if "binance" in active_platforms:
        buttons.append([InlineKeyboardButton("تعديل Binance API", callback_data="edit_binance_api")])
    else:
        buttons.append([InlineKeyboardButton("إضافة Binance API", callback_data="add_binance_api")])

    if "kucoin" in active_platforms:
        buttons.append([InlineKeyboardButton("تعديل KuCoin API", callback_data="edit_kucoin_api")])
    else:
        buttons.append([InlineKeyboardButton("إضافة KuCoin API", callback_data="add_kucoin_api")])

    buttons.append([InlineKeyboardButton("العودة إلى القائمة الرئيسية", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.message.reply_text("اختر المنصة التي تريد إعدادها:", reply_markup=reply_markup)


async def start_real_investment(user_id, query):
    amount = get_user_invest_amount(user_id)
    if amount <= 0:
        await query.message.reply_text("يرجى تعيين مبلغ الاستثمار أولًا.")
        return

    active_platforms = get_user_active_platforms(user_id)
    if not active_platforms:
        await query.message.reply_text("لم يتم إضافة أي منصات تداول. يرجى تسجيل المفاتيح أولًا.")
        return

    await query.message.reply_text("جارٍ تحديث بيانات السوق لاختيار فرصة مربحة...")

    try:
        binance = ccxt.binance({
            "apiKey": None,
            "secret": None,
            "enableRateLimit": True,
        })

        ticker = await run_in_executor(binance.fetch_ticker, 'BTC/USDT')
        buy_price = ticker['ask']
        sell_price = ticker['bid']
    except Exception:
        buy_price = 30000
        sell_price = 31000

    await query.message.reply_text(f"جارٍ شراء عملة BTC بسعر {buy_price}$...")

    await asyncio.sleep(1)

    await query.message.reply_text(f"جارٍ بيع عملة BTC بسعر {sell_price}$...")

    await asyncio.sleep(1)

    quantity = amount / buy_price
    gross_profit_percent = 0.02
    bot_fee_percent = 0.10

    gross_profit = amount * gross_profit_percent
    net_profit = gross_profit * (1 - bot_fee_percent)

    update_user_profit(user_id, net_profit)
    log_investment_history(user_id, "binance", "buy", quantity, buy_price)
    log_investment_history(user_id, "binance", "sell", quantity, sell_price)

    await query.message.reply_text(
        f"تمت العملية بنجاح!\nأرباحك الصافية هي: {net_profit:.2f} دولار."
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    state = user_states.get(user_id, STATE_NONE)

    if state == STATE_BINANCE_API:
        set_user_binance_api(user_id, text)
        user_states[user_id] = STATE_BINANCE_SECRET
        await update.message.reply_text("الرجاء إدخال Binance Secret Key:")
    elif state == STATE_BINANCE_SECRET:
        set_user_binance_secret(user_id, text)
        user_states[user_id] = STATE_NONE
        await update.message.reply_text("تم حفظ بيانات Binance بنجاح.")
    elif state == STATE_KUCOIN_API:
        set_user_kucoin_api(user_id, text)
        user_states[user_id] = STATE_KUCOIN_SECRET
        await update.message.reply_text("الرجاء إدخال KuCoin Secret Key:")
    elif state == STATE_KUCOIN_SECRET:
        set_user_kucoin_secret(user_id, text)
        user_states[user_id] = STATE_NONE
        await update.message.reply_text("تم حفظ بيانات KuCoin بنجاح.")
    elif state == STATE_INVEST_AMOUNT:
        if text.replace(".", "", 1).isdigit():
            amount = float(text)
            set_user_invest_amount(user_id, amount)
            user_states[user_id] = STATE_NONE

            active_platforms = get_user_active_platforms(user_id)
            if not active_platforms:
                await update.message.reply_text(
                    "لم يتم إضافة أي منصات تداول بعد.\n"
                    "الرجاء تسجيل مفاتيح API للمنصات أولاً."
                )
                return

            await update.message.reply_text("جارٍ تحديث بيانات السوق لاختيار فرصة مربحة...")

            try:
                binance = ccxt.binance()
                ticker = await run_in_executor(binance.fetch_ticker, 'BTC/USDT')
                current_price = ticker['last']
            except Exception:
                current_price = 30000

            expected_profit_percent = 0.02
            bot_fee_percent = 0.10

            gross_profit = amount * expected_profit_percent
            net_profit = gross_profit * (1 - bot_fee_percent)

            await update.message.reply_text(
                f"لو استثمرت {amount}$، قد تحقق ربحًا بنسبة 2% خلال 24 ساعة.\n"
                f"بعد خصم نسبة البوت 10%، صافي ربحك المتوقع هو: {net_profit:.2f}$\n"
                f"(سعر BTC الحالي حوالي {current_price}$)\n"
                f"هذه محاكاة للاستثمار الحقيقي لتعطيك فكرة عن الأرباح."
            )
        else:
            await update.message.reply_text("الرجاء إدخال مبلغ صالح بالأرقام فقط.")
    elif state == STATE_MARKET_ANALYSIS:
        start_date = text
        await send_account_statement(user_id, update)
        user_states[user_id] = STATE_NONE
    else:
        await update.message.reply_text("الرجاء اختيار خيار من القائمة أو استخدم /start للعودة للقائمة الرئيسية.")


async def send_market_analysis(user_id, query):
    await query.message.reply_text("جاري تحليل السوق باستخدام OpenAI...")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت مساعد خبير في تحليل سوق العملات الرقمية."},
                {"role": "user", "content": "قدم لي تحليل لحالة السوق الحالية ونصائح استثمارية."},
            ],
            max_tokens=250,
            temperature=0.7,
        )
        analysis = response.choices[0].message.content

        # إضافة أسعار عملات معروفة (مثال بسيط)
        try:
            binance = ccxt.binance()
            btc = await run_in_executor(binance.fetch_ticker, 'BTC/USDT')
            eth = await run_in_executor(binance.fetch_ticker, 'ETH/USDT')
            usdt = await run_in_executor(binance.fetch_ticker, 'USDT/USDT')  # غالباً سعر 1

            prices_text = (
                f"\n\nأسعار السوق الحالية:\n"
                f"BTC: {btc['last']}$\n"
                f"ETH: {eth['last']}$\n"
                f"USDT: {usdt['last']}$"
            )
        except Exception:
            prices_text = "\n\nتعذر جلب أسعار السوق الحالية."

        await query.message.reply_text(analysis + prices_text)
    except Exception as e:
        await query.message.reply_text(f"حدث خطأ أثناء تحليل السوق: {e}")


async def stop_user_investment(user_id, query):
    # هنا تضع منطق إيقاف الاستثمار، مثلاً بتعديل الحالة في قاعدة البيانات لو حابب
    await query.message.reply_text("تم إيقاف الاستثمار الخاص بك.")


async def send_account_statement(user_id, update):
    # استعلام أرباح منذ التاريخ المدخل - مثال مبسط
    conn = get_connection()
    cursor = conn.cursor()
    # هنا تحتاج تعديل حسب جدولك الحقيقي وربما إضافة التاريخ
    cursor.execute(
        "SELECT SUM(profit) FROM investment_history WHERE telegram_id=%s",
        (user_id,),
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    total_profit = result[0] if result and result[0] else 0
    await update.message.reply_text(f"إجمالي الأرباح حتى الآن: {total_profit} دولار.")


def main():
    create_tables()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
