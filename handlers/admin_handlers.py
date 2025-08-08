from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

def setup_admin_handlers(application):
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        await update.message.reply_text("❌ ليس لديك صلاحية الوصول إلى لوحة الإدارة.")
        return

    keyboard = [
        [InlineKeyboardButton("📊 حالة التداول", callback_data="admin_trading_status")],
        [InlineKeyboardButton("🔁 إعادة تشغيل البوت", callback_data="admin_restart")],
        [InlineKeyboardButton("📈 تقارير الأداء", callback_data="admin_reports")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👨‍💼 لوحة الإدارة:", reply_markup=reply_markup)

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "admin_trading_status":
        trade_executor = context.bot_data.get("trade_executor")
        if trade_executor:
            is_active = trade_executor.is_trading_active()
            await query.edit_message_text(f"🔄 التداول {'مفعل ✅' if is_active else 'معطل ❌'}")
        else:
            await query.edit_message_text("⚠️ لا يمكن الوصول إلى حالة التداول.")

    elif query.data == "admin_restart":
        await query.edit_message_text("🔁 يتم الآن إعادة تشغيل البوت... (وهمية)")
        # هنا يمكن تنفيذ منطق إعادة التشغيل الحقيقي لاحقاً

    elif query.data == "admin_reports":
        await query.edit_message_text("📈 التقارير غير مفعلة بعد. (placeholder)")