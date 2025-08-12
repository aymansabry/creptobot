# handlers.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
import database
import utils

logger = logging.getLogger(__name__)

# المراحل للحوار
(
    CHOOSING_ACTION,
    ENTER_API_KEY,
    ENTER_API_SECRET,
    CHOOSE_PLATFORM,
    ENTER_INVEST_AMOUNT,
    CHOOSE_INVEST_TYPE,
    ENTER_START_DATE,
    ENTER_END_DATE,
    CONFIRM_INVEST,
    # ...
) = range(10)

# قائمة المنصات المتاحة - نفس اللي في utils مع دعم sandbox
PLATFORMS = ['binance', 'kucoin']

# تخزين بيانات المستخدم مؤقتا أثناء الحوار (يمكن استبدالها بقاعدة أو كاش)
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["تسجيل/تعديل بيانات التداول"],
        ["ابدأ استثمار"],
        ["استثمار وهمي"],
        ["كشف حساب عن فترة"],
        ["حالة السوق"],
        ["إيقاف الاستثمار"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "اختر العملية التي تريد القيام بها:", reply_markup=reply_markup
    )
    return CHOOSING_ACTION

# تسجيل أو تعديل API Keys
async def trading_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(p.capitalize(), callback_data=p)] for p in PLATFORMS]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر المنصة التي تريد إضافة أو تعديل بياناتها:", reply_markup=reply_markup)
    return CHOOSE_PLATFORM

async def choose_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    platform = query.data
    context.user_data['platform'] = platform
    await query.edit_message_text(f"أدخل API Key الخاصة بمنصة {platform.capitalize()}:")
    return ENTER_API_KEY

async def enter_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = update.message.text.strip()
    context.user_data['api_key'] = api_key
    await update.message.reply_text(f"الآن أدخل الـ API Secret لمنصة {context.user_data['platform'].capitalize()}:")
    return ENTER_API_SECRET

async def enter_api_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_secret = update.message.text.strip()
    platform = context.user_data['platform']
    api_key = context.user_data['api_key']

    # تحقق من صحة المفاتيح
    is_valid = utils.validate_api_keys(platform, api_key, api_secret)
    if is_valid:
        database.save_user_platform(
            telegram_id=update.message.from_user.id,
            platform=platform,
            api_key=api_key,
            api_secret=api_secret,
            active=True
        )
        await update.message.reply_text(f"تم حفظ بيانات منصة {platform.capitalize()} بنجاح ✅", reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text(f"مفاتيح API غير صحيحة أو غير صالحة. الرجاء المحاولة مرة أخرى أو إلغاء العملية.", reply_markup=ReplyKeyboardRemove())

    return await start(update, context)

# بدء الاستثمار
async def start_invest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_platforms = database.get_user_platforms(update.message.from_user.id, only_active=True)
    if not user_platforms:
        await update.message.reply_text("لم تقم بإضافة أي منصات تداول بعد. الرجاء تسجيل منصات التداول أولاً.")
        return await start(update, context)

    await update.message.reply_text("حدد مبلغ الاستثمار (بالدولار):")
    return ENTER_INVEST_AMOUNT

async def enter_invest_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        if amount <= 0:
            raise ValueError()
        context.user_data['invest_amount'] = amount
    except ValueError:
        await update.message.reply_text("الرجاء إدخال مبلغ صالح أكبر من صفر.")
        return ENTER_INVEST_AMOUNT

    # نعرض للمستخدم نوع الاستثمار: وهمي أم حقيقي
    keyboard = [["استثمار وهمي"], ["استثمار حقيقي"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("اختر نوع الاستثمار:", reply_markup=reply_markup)
    return CHOOSE_INVEST_TYPE

async def choose_invest_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    invest_type = update.message.text
    if invest_type not in ["استثمار وهمي", "استثمار حقيقي"]:
        await update.message.reply_text("اختر استثمار وهمي أو استثمار حقيقي فقط.")
        return CHOOSE_INVEST_TYPE

    context.user_data['invest_type'] = invest_type

    # تحقق من رصيد المحافظ
    if invest_type == "استثمار حقيقي":
        # تحقق الرصيد في المحافظ (مثال: يجمع أرصدة جميع المنصات)
        total_balance = database.get_total_user_balance(update.message.from_user.id)
        invest_amount = context.user_data['invest_amount']
        if invest_amount > total_balance:
            await update.message.reply_text(
                f"رصيدك في المحافظ غير كافي للاستثمار بالمبلغ المطلوب ({invest_amount}$).\n"
                "يمكنك الاستثمار بالمبلغ المتاح أو إعادة إيداع رصيد."
                "\nهل تريد الاستثمار بالمبلغ المتاح؟ (نعم / لا)"
            )
            return CONFIRM_INVEST
        else:
            await update.message.reply_text("جارٍ بدء الاستثمار...")
            return await perform_investment(update, context)

    else:  # وهمي
        await update.message.reply_text("جارٍ بدء الاستثمار الوهمي (بدون استخدام أموال حقيقية)...")
        return await perform_investment(update, context)

async def confirm_invest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip().lower()
    if answer == "نعم":
        # نستخدم المبلغ المتاح
        invest_amount = database.get_total_user_balance(update.message.from_user.id)
        context.user_data['invest_amount'] = invest_amount
        await update.message.reply_text(f"سيتم الاستثمار بالمبلغ المتاح: {invest_amount}$")
        return await perform_investment(update, context)
    else:
        await update.message.reply_text("تم إلغاء الاستثمار. يمكنك المحاولة لاحقاً.")
        return await start(update, context)

async def perform_investment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    amount = context.user_data['invest_amount']
    invest_type = context.user_data['invest_type']

    # السيناريو حسب نوع الاستثمار
    await update.message.reply_text(f"حدد المبلغ: {amount} دولار")
    await update.message.reply_text("جاري التحقق من المنصات...")

    user_platforms = database.get_user_platforms(user_id, only_active=True)
    if not user_platforms:
        await update.message.reply_text("لم يتم العثور على منصات تداول نشطة، الرجاء إضافة منصات التداول أولاً.")
        return await start(update, context)

    await update.message.reply_text("جاري جلب الأسعار لاختيار فرصة مربحة...")

    # هنا مكان تنفيذ المراجحة أو محاكاة وهمية حسب النوع
    # مثال مبسط:
    for platform in user_platforms:
        exchange = utils.get_exchange(platform['platform'], platform['api_key'], platform['api_secret'])
        symbol = 'BTC/USDT'
        try:
            price = exchange.fetch_ticker(symbol)['last']
            await update.message.reply_text(f"منصة {platform['platform'].capitalize()}: سعر {symbol} الحالي {price}$")
            # شراء وبيع وهمي/حقيقي
            await update.message.reply_text(f"جاري تنفيذ شراء {symbol}...")
            if invest_type == "استثمار حقيقي":
                order = utils.place_market_order(exchange, symbol, 'buy', amount / price)
            else:
                order = {"sandbox": True, "symbol": symbol, "side": "buy", "amount": amount / price}
            await update.message.reply_text(f"جاري تنفيذ بيع {symbol}...")
            if invest_type == "استثمار حقيقي":
                order = utils.place_market_order(exchange, symbol, 'sell', amount / price)
            else:
                order = {"sandbox": True, "symbol": symbol, "side": "sell", "amount": amount / price}

            profit, fee = utils.calculate_profit(amount * 0.05)  # نفترض 5% ربح كأمثلة
            await update.message.reply_text(f"تمت العملية بنجاح. أرباحك هي {profit}$ بعد خصم عمولة البوت {fee}$")
        except Exception as e:
            await update.message.reply_text(f"حدث خطأ في منصة {platform['platform'].capitalize()}: {str(e)}")

    return await start(update, context)

# كشف حساب حسب فترة (يطالب بالتاريخ)
async def account_statement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل بداية الفترة (YYYY-MM-DD):")
    return ENTER_START_DATE

async def enter_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['start_date'] = update.message.text.strip()
    await update.message.reply_text("أرسل نهاية الفترة (YYYY-MM-DD):")
    return ENTER_END_DATE

async def enter_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['end_date'] = update.message.text.strip()
    user_id = update.message.from_user.id
    start_date = context.user_data['start_date']
    end_date = context.user_data['end_date']
    report = database.get_account_statement(user_id, start_date, end_date)
    if not report:
        await update.message.reply_text("لا توجد بيانات في هذه الفترة.")
    else:
        # نفترض التقرير نصي
        await update.message.reply_text(report)
    return await start(update, context)

# حالة السوق مع نصيحة
async def market_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analysis, prices = database.get_market_analysis()
    message = f"تحليل السوق:\n{analysis}\n\nأسعار العملات الحالية:\n"
    for symbol, price in prices.items():
        message += f"{symbol}: {price}$\n"
    message += "\nنصيحة: استثمر بحكمة وتابع الأخبار دائماً."
    await update.message.reply_text(message)
    return await start(update, context)

# إيقاف الاستثمار
async def stop_investment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.set_investment_active(update.message.from_user.id, False)
    await update.message.reply_text("تم إيقاف الاستثمار الخاص بك. لن يتم استخدام أموالك في عمليات التداول حتى تقوم بإعادة تفعيلها.")
    return await start(update, context)

# إلغاء العملية
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def register_handlers(application):
    from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_ACTION: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), start),
                MessageHandler(filters.Regex('^(تسجيل/تعديل بيانات التداول)$'), trading_data),
                MessageHandler(filters.Regex('^(ابدأ استثمار)$'), start_invest),
                MessageHandler(filters.Regex('^(استثمار وهمي)$'), start_invest),
                MessageHandler(filters.Regex('^(كشف حساب عن فترة)$'), account_statement),
                MessageHandler(filters.Regex('^(حالة السوق)$'), market_status),
                MessageHandler(filters.Regex('^(إيقاف الاستثمار)$'), stop_investment),
            ],
            CHOOSE_PLATFORM: [CallbackQueryHandler(choose_platform)],
            ENTER_API_KEY: [MessageHandler(filters.TEXT & (~filters.COMMAND), enter_api_key)],
            ENTER_API_SECRET: [MessageHandler(filters.TEXT & (~filters.COMMAND), enter_api_secret)],
            ENTER_INVEST_AMOUNT: [MessageHandler(filters.TEXT & (~filters.COMMAND), enter_invest_amount)],
            CHOOSE_INVEST_TYPE: [MessageHandler(filters.Regex('^(استثمار وهمي|استثمار حقيقي)$'), choose_invest_type)],
            CONFIRM_INVEST: [MessageHandler(filters.Regex('^(نعم|لا)$'), confirm_invest)],
            ENTER_START_DATE: [MessageHandler(filters.TEXT & (~filters.COMMAND), enter_start_date)],
            ENTER_END_DATE: [MessageHandler(filters.TEXT & (~filters.COMMAND), enter_end_date)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
