from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

def setup_user_handlers(application):
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(user_menu_handler, pattern="^user_"))

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_session_factory = context.bot_data["db_session"]

    # حفظ المستخدم في قاعدة البيانات إذا لم يكن موجودًا
    from db.models import User
    async with db_session_factory() as session:
        user = await session.get(User, user_id)
        if not user:
            session.add(User(id=user_id, balance=100, investment=0))
            await session.commit()

    keyboard = [
        [InlineKeyboardButton("📈 بدء التداول", callback_data="trade_start")],
        [InlineKeyboardButton("💼 محفظتي", callback_data="trade_portfolio")],
        [InlineKeyboardButton("💸 استثمار الآن", callback_data="trade_invest")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 أهلاً بك في بوت التداول.\nاختر من القائمة:", reply_markup=reply_markup)

async def user_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # هذا القسم لم يعد يُستخدم لأن الأزرار تدار من trade_handlers مباشرة.
    await query.edit_message_text("❌ أمر غير معروف. يرجى استخدام الأزرار المتاحة.")