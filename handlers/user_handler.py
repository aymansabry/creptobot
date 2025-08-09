from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from db.session import get_session
from db.models import User

# استدعاء جلسة قاعدة البيانات
def get_user(session, telegram_id: str):
    return session.query(User).filter_by(telegram_id=telegram_id).first()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or ""

    session = get_session()
    user = get_user(session, user_id)
    if not user:
        # تسجيل مستخدم جديد
        new_user = User(telegram_id=user_id, username=username)
        session.add(new_user)
        session.commit()

    # عرض قائمة (يمكن تعديلها حسب حاجتك)
    keyboard = [
        [InlineKeyboardButton("بدء الاستثمار", callback_data="start_invest")],
        [InlineKeyboardButton("الحسابات", callback_data="accounts")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("مرحباً! اختر ما تريد:", reply_markup=reply_markup)
    session.close()

start_handler = CommandHandler("start", start)

async def handle_user_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "start_invest":
        await query.edit_message_text("أدخل مبلغ الاستثمار (مثلاً: 10):")
        context.user_data["awaiting_amount"] = True
    elif data == "accounts":
        await query.edit_message_text("هنا صفحة الحسابات (قيد التطوير).")

handle_user_selection = CallbackQueryHandler(handle_user_selection)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_amount"):
        amount_text = update.message.text
        try:
            amount = float(amount_text)
            if amount < 1:
                await update.message.reply_text("المبلغ يجب أن يكون 1 USDT على الأقل.")
                return
            # تخزين المبلغ للمستخدم (يمكن تعديلها لتخزين في DB)
            context.user_data["investment_amount"] = amount
            context.user_data["awaiting_amount"] = False
            await update.message.reply_text(f"تم تحديد مبلغ الاستثمار: {amount} USDT")
        except ValueError:
            await update.message.reply_text("الرجاء إدخال رقم صحيح.")
    else:
        await update.message.reply_text("استخدم القائمة لبدء الاستثمار.")

text_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler)
