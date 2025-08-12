import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import ccxt.async_support as ccxt
from dotenv import load_dotenv
import openai
import asyncio
from database import (
    create_tables,
    run_in_threadpool,
    db_get_user_api_keys,
    db_set_user_binance_api,
    db_set_user_binance_secret,
    db_set_user_kucoin_api,
    db_set_user_kucoin_secret,
    db_set_user_kucoin_password,
    db_set_user_invest_amount,
    db_get_user_profit,
    db_set_user_investing_status,
    db_get_active_platforms,
    db_insert_investment_history,
    db_get_account_statement,
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# User States
(
    STATE_NONE,
    STATE_BINANCE_API,
    STATE_BINANCE_SECRET,
    STATE_KUCOIN_API,
    STATE_KUCOIN_SECRET,
    STATE_KUCOIN_PASSWORD,
    STATE_INVEST_AMOUNT,
    STATE_START_INVEST,
    STATE_START_VIRTUAL_INVEST,
    STATE_MARKET_ANALYSIS,
) = range(10)

user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1. تسجيل أو تعديل بيانات التداول", callback_data="manage_trading")],
        [InlineKeyboardButton("2. بدء استثمار حقيقي", callback_data="start_invest")],
        [InlineKeyboardButton("3. استثمار وهمي", callback_data="virtual_invest")],
        [InlineKeyboardButton("4. كشف حساب عن فترة", callback_data="account_statement")],
        [InlineKeyboardButton("5. حالة السوق", callback_data="market_status")],
        [InlineKeyboardButton("6. إيقاف الاستثمار", callback_data="stop_invest")],
        [InlineKeyboardButton("القائمة الرئيسية", callback_data="main_menu")],
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
        await query.message.reply_text("جاري بدء الاستثمار الوهمي بأسعار حقيقية (بدون تنفيذ صفقات)...")
        await start_virtual_investment(user_id, query)
    elif query.data == "account_statement":
        user_states[user_id] = STATE_MARKET_ANALYSIS
        await query.message.reply_text("أرسل بداية الفترة (YYYY-MM-DD):")
    elif query.data == "market_status":
        await send_market_analysis(user_id, query)
    elif query.data == "stop_invest":
        await stop_user_investment(user_id, query)
    elif query.data == "main_menu":
        await start(query, context)
    else:
        await query.message.reply_text("أمر غير معروف، الرجاء اختيار من القائمة.")

async def manage_trading_menu(query, user_id):
    active_platforms = await run_in_threadpool(db_get_active_platforms, user_id)
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

# التحقق من صلاحية مفاتيح API
async def validate_api_keys(user_id):
    row = await run_in_threadpool(db_get_user_api_keys, user_id)
    if not row:
        return False
    binance_api, binance_secret, kucoin_api, kucoin_secret, kucoin_password = row

    try:
        binance = ccxt.binance({
            "apiKey": binance_api,
            "secret": binance_secret,
            "enableRateLimit": True,
        })
        await binance.load_markets()
        await binance.fetch_balance()
        await binance.close()
    except Exception as e:
        logger.error(f"Binance API Error: {e}")
        return False

    try:
        kucoin = ccxt.kucoin({
            "apiKey": kucoin_api,
            "secret": kucoin_secret,
            "password": kucoin_password,
            "enableRateLimit": True,
        })
        await kucoin.load_markets()
        await kucoin.fetch_balance()
        await kucoin.close()
    except Exception as e:
        logger.error(f"KuCoin API Error: {e}")
        return False

    return True

async def start_real_investment(user_id, query):
    valid = await validate_api_keys(user_id)
    if not valid:
        await query.message.reply_text("مفاتيح API غير صحيحة أو غير مكتملة. يرجى التحقق أولاً.")
        return

    await run_real_trading_algorithm(user_id, query)

async def run_real_trading_algorithm(user_id, query):
    # خوارزمية مراجحة بسيطة على Binance - نموذجية للشرح فقط

    row = await run_in_threadpool(db_get_user_api_keys, user_id)
    binance_api, binance_secret, _, _, _ = row
    binance = ccxt.binance({
        "apiKey": binance_api,
        "secret": binance_secret,
        "enableRateLimit": True,
    })

    try:
        balance = await binance.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        amount_to_invest = await run_in_threadpool(db_get_user_invest_amount, user_id)
        if amount_to_invest is None or amount_to_invest <= 0:
            amount_to_invest = 10  # مبلغ افتراضي

        if usdt_balance < amount_to_invest:
            await query.message.reply_text(f"رصيد USDT غير كافٍ. لديك {usdt_balance} USDT فقط.")
            await binance.close()
            return

        symbol = "BTC/USDT"
        ticker = await binance.fetch_ticker(symbol)
        last_price = ticker['last']

        # تنفيذ شراء BTC بمبلغ amount_to_invest
        quantity = amount_to_invest / last_price
        quantity = binance.amount_to_precision(symbol, quantity)

        order = await binance.create_market_buy_order(symbol, float(quantity))
        await query.message.reply_text(f"تم شراء {quantity} BTC بسعر {last_price} USDT.")

        # تسجيل الصفقة في التاريخ
        await run_in_threadpool(db_insert_investment_history, user_id, "binance", "buy", amount_to_invest, last_price)

        # يمكنك هنا إضافة مزيد من الخوارزميات (بيع، مراجحة، إلخ)

    except Exception as e:
        await query.message.reply_text(f"خطأ أثناء تنفيذ التداول الحقيقي: {e}")
    finally:
        await binance.close()

async def start_virtual_investment(user_id, query):
    # استثمار وهمي بأسعار حقيقية بدون تنفيذ صفقات

    row = await run_in_threadpool(db_get_user_api_keys, user_id)
    binance_api, binance_secret, _, _, _ = row

    binance = ccxt.binance({
        "apiKey": binance_api or "",
        "secret": binance_secret or "",
        "enableRateLimit": True,
    })

    try:
        symbols = ["BTC/USDT", "ETH/USDT"]
        prices = {}
        for sym in symbols:
            ticker = await binance.fetch_ticker(sym)
            prices[sym] = ticker['last']

        invested_amount = await run_in_threadpool(db_get_user_invest_amount, user_id)
        if not invested_amount or invested_amount <= 0:
            invested_amount = 1000

        # محاكاة بسيطة: شراء العملات بنسبة متساوية من المبلغ المستثمر
        num_symbols = len(symbols)
        each_invest = invested_amount / num_symbols

        results = []
        for sym in symbols:
            qty = each_invest / prices[sym]
            results.append(f"تم شراء وهمي لـ {qty:.6f} من {sym} بسعر {prices[sym]}")

        report = "\n".join(results)
        await query.message.reply_text(f"الاستثمار الوهمي باستخدام الأسعار الحالية:\n{report}")

    except Exception as e:
        await query.message.reply_text(f"❌ حدث خطأ أثناء الاستثمار الوهمي: {e}")
    finally:
        await binance.close()

async def send_market_analysis(user_id, query):
    await query.message.reply_text("جاري تحليل السوق...")

    # جلب أسعار العملات
    binance = ccxt.binance()
    try:
        symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "XRP/USDT"]
        prices = {}
        for sym in symbols:
            ticker = await binance.fetch_ticker(sym)
            prices[sym] = ticker['last']

        # بناء نص التقرير
        price_report = "\n".join([f"{sym}: {prices[sym]}" for sym in symbols])
        prompt = f"""أنت مساعد خبير في العملات الرقمية. أسعار العملات الحالية هي:
{price_report}

قدم لي تحليل موجز ونصائح تداول استنادًا إلى الأسعار الحالية."""

        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت خبير تداول العملات الرقمية."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=400,
        )

        advice = response.choices[0].message.content
        full_report = f"تقرير أسعار العملات:\n{price_report}\n\nنصائح التداول:\n{advice}"
        await query.message.reply_text(full_report)

    except Exception as e:
        await query.message.reply_text(f"❌ خطأ أثناء تحليل السوق: {e}")
    finally:
        await binance.close()

async def stop_user_investment(user_id, query):
    await run_in_threadpool(db_set_user_investing_status, user_id, False)
    await query.message.reply_text("تم إيقاف الاستثمار الخاص بك.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    state = user_states.get(user_id, STATE_NONE)

    if state == STATE_BINANCE_API:
        await run_in_threadpool(db_set_user_binance_api, user_id, text)
        user_states[user_id] = STATE_BINANCE_SECRET
        await update.message.reply_text("أرسل مفتاح Binance السري:")
    elif state == STATE_BINANCE_SECRET:
        await run_in_threadpool(db_set_user_binance_secret, user_id, text)
        user_states[user_id] = STATE_KUCOIN_API
        await update.message.reply_text("أرسل مفتاح KuCoin العام (API Key):")
    elif state == STATE_KUCOIN_API:
        await run_in_threadpool(db_set_user_kucoin_api, user_id, text)
        user_states[user_id] = STATE_KUCOIN_SECRET
        await update.message.reply_text("أرسل مفتاح KuCoin السري (Secret Key):")
    elif state == STATE_KUCOIN_SECRET:
        await run_in_threadpool(db_set_user_kucoin_secret, user_id, text)
        user_states[user_id] = STATE_KUCOIN_PASSWORD
        await update.message.reply_text("أرسل كلمة مرور KuCoin:")
    elif state == STATE_KUCOIN_PASSWORD:
        await run_in_threadpool(db_set_user_kucoin_password, user_id, text)
        user_states[user_id] = STATE_INVEST_AMOUNT
        await update.message.reply_text("أرسل مبلغ الاستثمار بالدولار (مثلاً: 100):")
    elif state == STATE_INVEST_AMOUNT:
        try:
            amount = float(text)
            await run_in_threadpool(db_set_user_invest_amount, user_id, amount)
            user_states[user_id] = STATE_NONE
            await update.message.reply_text(f"تم حفظ مبلغ الاستثمار: {amount} دولار.")
        except Exception:
            await update.message.reply_text("يرجى إدخال رقم صحيح للمبلغ.")
    elif state == STATE_MARKET_ANALYSIS:
        # استقبال تاريخ بداية الفترة لحساب كشف الحساب
        try:
            from datetime import datetime

            start_date = datetime.strptime(text, "%Y-%m-%d")
            profit = await run_in_threadpool(db_get_account_statement, user_id, start_date)
            await update.message.reply_text(
                f"إجمالي الأرباح منذ {text}: {profit} دولار"
            )
            user_states[user_id] = STATE_NONE
        except Exception:
            await update.message.reply_text(
                "يرجى إدخال التاريخ بصيغة صحيحة: YYYY-MM-DD"
            )
    else:
        await update.message.reply_text("الرجاء استخدام القائمة لتحديد خيار.")

def main():
    create_tables()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

    app.run_polling()

if __name__ == "__main__":
    main()
