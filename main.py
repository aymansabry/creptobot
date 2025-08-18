#main.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import Config
import os

# الدالة الخاصة بأمر /start
async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("🔄 ربط الحسابات", callback_data='connect')],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data='stats')]
    ]
    await update.message.reply_text(
        "القائمة الرئيسية:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# الدالة الخاصة بالتعامل مع الأزرار
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

# الدالة الرئيسية لتشغيل البوت
def main():
    # هنا تم التعديل
    # بدل ما كان بياخد "TOKEN"، أصبح بيجيب التوكن من متغير البيئة
    app = Application.builder().token(Config.BOT_TOKEN).build()
    
    # إضافة المعالجات للأوامر والأزرار
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    
    # تشغيل البوت
    app.run_polling()

if __name__ == '__main__':
    main()
