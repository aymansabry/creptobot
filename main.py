from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("🔄 ربط الحسابات", callback_data='connect')],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data='stats')]
    ]
    await update.message.reply_text(
        "القائمة الرئيسية:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_buttons(update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'connect':
        keyboard = [
            [InlineKeyboardButton("بينانس", callback_data='binance')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='back')]
        ]
        await query.edit_message_text(
            text="اختر المنصة:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif query.data == 'back':
        await start(update, context)

def main():
    app = Application.builder().token("TOKEN").build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    
    app.run_polling()

if __name__ == '__main__':
    main()