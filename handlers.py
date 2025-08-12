# handlers.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

import database
from utils import (
    create_exchange_client, fetch_current_price,
    calculate_profit, execute_market_order,
    get_bot_fee_percent,
)
from database import SessionLocal

logger = logging.getLogger(__name__)

# مراحل المحادثة للـ ConversationHandler
(
    CHOOSE_MENU,
    ENTER_API_KEY,
    ENTER_API_SECRET,
    CHOOSE_PLATFORM,
    ENTER_INVESTMENT_AMOUNT,
    CHOOSE_INVESTMENT_TYPE,
    ENTER_START_DATE,
    ENTER_END_DATE,
) = range(8)

# قائمة رئيسية للمستخدم
def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("1. تسجيل/تعديل بيانات التداول", callback_data='trade_data')],
        [InlineKeyboardButton("2. ابدأ استثمار", callback_data='start_invest')],
        [InlineKeyboardButton("3. استثمار وهمي", callback_data='dummy_invest')],
        [InlineKeyboardButton("4. كشف حساب عن فترة", callback_data='account_statement')],
        [InlineKeyboardButton("5. حالة السوق", callback_data='market_status')],
        [InlineKeyboardButton("6. إيقاف الاستثمار", callback_data='stop_invest')],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"مرحباً {user.first_name}!\nاختر من القائمة الرئيسية:",
        reply_markup=get_main_menu_keyboard()
    )
    return CHOOSE_MENU

# -- التسجيل / تعديل مفاتيح API --
async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == 'trade_data':
        # عرض المنصات المسجلة للمستخدم مع خيارات إضافة/تعديل/حذف
        user_id = query.from_user.id
        with SessionLocal() as db:
            platforms = database.get_user_platforms(db, user_id)
        if not platforms:
            await query.edit_message_text("لا توجد منصات مسجلة بعد.\nاضغط /add_platform لإضافة منصة.")
            return CHOOSE_MENU
        buttons = []
        for p in platforms:
            buttons.append([InlineKeyboardButton(f"{p['exchange']} (مفعل)" if p['active'] else f"{p['exchange']} (موقف)", callback_data=f"edit_platform_{p['id']}")])
        buttons.append([InlineKeyboardButton("➕ إضافة منصة جديدة", callback_data='add_platform')])
        buttons.append([InlineKeyboardButton("⬅️ رجوع للقائمة الرئيسية", callback_data='main_menu')])
        await query.edit_message_text("منصات التداول الخاصة بك:", reply_markup=InlineKeyboardMarkup(buttons))
        return CHOOSE_PLATFORM

    elif choice == 'add_platform':
        await query.edit_message_text("أرسل اسم المنصة (مثل: binance أو kucoin):")
        return ENTER_API_KEY  # الخطوة التالية لإدخال الـ API key

    elif choice == 'start_invest':
        # بداية استثمار حقيقي
        await query.edit_message_text("حدد مبلغ الاستثمار:")
        return ENTER_INVESTMENT_AMOUNT

    elif choice == 'dummy_invest':
        await query.edit_message_text("حدد مبلغ الاستثمار الوهمي:")
        return ENTER_INVESTMENT_AMOUNT

    elif choice == 'account_statement':
        await query.edit_message_text("أرسل بداية الفترة (YYYY-MM-DD):")
        return ENTER_START_DATE

    elif choice == 'market_status':
        # هنا يمكن تنفيذ تحليل السوق وارسال النص + اسعار العملات
        text_analysis = await get_market_analysis()
        await query.edit_message_text(text_analysis[:4000])  # فقط جزء من الرسالة مع قص في حالة الطول الزائد
        return CHOOSE_MENU

    elif choice == 'stop_invest':
        user_id = query.from_user.id
        with SessionLocal() as db:
            database.stop_investment_for_user(db, user_id)
        await query.edit_message_text("تم إيقاف الاستثمار لديك. لن يتم استخدام أموالك في استثمارات جديدة حتى تطلب ذلك.")
        return CHOOSE_MENU

    elif choice == 'main_menu':
        await query.edit_message_text("القائمة الرئيسية:", reply_markup=get_main_menu_keyboard())
        return CHOOSE_MENU

    else:
        await query.edit_message_text("اختيار غير معروف، الرجاء المحاولة مرة أخرى.")
        return CHOOSE_MENU

async def add_platform_receive_exchange_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    context.user_data['new_platform_exchange'] = text
    await update.message.reply_text("الآن، أرسل مفتاح API الخاص بالمنصة:")
    return ENTER_API_SECRET

async def add_platform_receive_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data['new_platform_api_key'] = text
    await update.message.reply_text("أرسل الآن الـ API Secret:")
    return CHOOSE_PLATFORM

async def add_platform_receive_api_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data['new_platform_api_secret'] = text
    user_id = update.message.from_user.id
    exchange = context.user_data.get('new_platform_exchange')
    api_key = context.user_data.get('new_platform_api_key')
    api_secret = text
    # تحقق من صلاحية المفاتيح
    try:
        client = create_exchange_client(exchange, api_key, api_secret)
        await update.message.reply_text("جارِ التحقق من صحة المفاتيح...")
        await client.load_markets()
    except Exception as e:
        await update.message.reply_text(f"مفاتيح غير صالحة أو خطأ في الاتصال: {e}\nأرسل مفتاح API مرة أخرى:")
        return ENTER_API_SECRET
    # إذا نجح
    with SessionLocal() as db:
        database.add_user_platform(db, user_id, exchange, api_key, api_secret, active=True)
    await update.message.reply_text(f"تم إضافة منصة {exchange} بنجاح!")
    return CHOOSE_MENU

# تنفيذ استثمار وهمي أو حقيقي
async def receive_investment_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError()
    except:
        await update.message.reply_text("الرجاء إدخال مبلغ صالح أكبر من صفر.")
        return ENTER_INVESTMENT_AMOUNT
    context.user_data['investment_amount'] = amount
    await update.message.reply_text("اختر نوع الاستثمار:\n1. استثمار حقيقي\n2. استثمار وهمي", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("استثمار حقيقي", callback_data="real_invest")],
        [InlineKeyboardButton("استثمار وهمي", callback_data="dummy_invest")],
    ]))
    return CHOOSE_INVESTMENT_TYPE

async def handle_investment_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    invest_type = query.data
    amount = context.user_data.get('investment_amount')
    user_id = query.from_user.id
    # تحقق من الرصيد لو استثمار حقيقي
    if invest_type == "real_invest":
        with SessionLocal() as db:
            platforms = database.get_user_platforms(db, user_id, active_only=True)
            if not platforms:
                await query.edit_message_text("لا توجد منصات مفعلة للاستثمار الحقيقي، يرجى إضافة منصة على الأقل.")
                return CHOOSE_MENU
            # تأكد من وجود رصيد كافي (نفرض دالة لفحص الرصيد)
            total_balance = 0
            for p in platforms:
                try:
                    client = create_exchange_client(p['exchange'], p['api_key'], p['api_secret'])
                    balance = client.fetch_balance()
                    total_balance += balance['total'].get('USDT', 0)  # مثال على USDT فقط
                except:
                    continue
            if total_balance < amount:
                await query.edit_message_text(f"رصيدك الحالي في المحفظة: {total_balance} USDT وهو أقل من مبلغ الاستثمار المطلوب {amount} USDT.\nيرجى إيداع المزيد ثم المحاولة مجددًا.")
                return CHOOSE_MENU
        await query.edit_message_text(f"تم تعيين مبلغ الاستثمار: {amount} دولار\nابدأ الاستثمار من القائمة.")
        # احفظ حالة الاستثمار الحقيقية وابدأ عملية التداول حسب الخوارزميات
        # ... (تحتاج لتكامل مع خوارزمية التداول الفعلية هنا)
    else:
        await query.edit_message_text(f"تم تعيين المبلغ الوهمي: {amount} دولار\nابدأ الاستثمار الوهمي من القائمة.")
        # احفظ حالة الاستثمار الوهمي وابدأ المحاكاة

    return CHOOSE_MENU

async def get_market_analysis():
    # هنا استدعاء API تحليل السوق أو خوارزمية ذكاء اصطناعي
    analysis_text = (
        "تحليل السوق الحالي:\n"
        "- البيتكوين: 29000 دولار\n"
        "- الإيثيريوم: 1800 دولار\n"
        "- توصية: انتبه لتقلبات السوق الحالية\n"
    )
    return analysis_text

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية، يمكنك البدء من جديد باستخدام /start.")
    return ConversationHandler.END


def register_handlers(application):
    from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters, ConversationHandler

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_MENU: [CallbackQueryHandler(handle_menu_choice)],
            ENTER_API_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_platform_receive_exchange_name)],
            ENTER_API_SECRET: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_platform_receive_api_key)],
            CHOOSE_PLATFORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_platform_receive_api_secret)],
            ENTER_INVESTMENT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_investment_amount)],
            CHOOSE_INVESTMENT_TYPE: [CallbackQueryHandler(handle_investment_type)],
            ENTER_START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u,c: c.user_data.update({'start_date': u.message.text}) or get_end_date(u,c))],
            # يمكن إضافة مزيد من الحالات حسب الطلب
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(conv_handler)

async def get_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل نهاية الفترة (YYYY-MM-DD):")
    return ENTER_END_DATE
