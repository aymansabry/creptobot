from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

def setup_admin_handlers(application):
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CallbackQueryHandler(handle_admin_buttons))

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_ids = context.bot_data.get("admin_ids", [])
    user_id = update.effective_user.id

    if user_id not in admin_ids:
        await update.message.reply_text("❌ ليس لديك صلاحية الوصول إلى لوحة الإدارة.")
        return

    keyboard = [
        [InlineKeyboardButton("📊 عرض الإحصائيات", callback_data="show_stats")],
        [InlineKeyboardButton("🚀 بدء التداول", callback_data="start_trading")],
        [InlineKeyboardButton("🛑 إيقاف التداول", callback_data="stop_trading")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("✅ مرحبًا بك في لوحة التحكم الإدارية:", reply_markup=reply_markup)

async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "show_stats":
        # مثال بسيط — في المشروع الفعلي: احصل على بيانات من قاعدة البيانات أو redis
        await query.edit_message_text("📊 الإحصائيات:\n- المستخدمون: 10\n- الصفقات المنفذة: 45\n- التداول مفعل ✅")
    elif data == "start_trading":
        context.bot_data["trading_active"] = True
        await query.edit_message_text("🚀 تم تفعيل التداول.")
    elif data == "stop_trading":
        context.bot_data["trading_active"] = False
        await query.edit_message_text("🛑 تم إيقاف التداول.")
    else:
        await query.edit_message_text("❓ أمر غير معروف.")