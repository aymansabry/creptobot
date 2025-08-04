from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
import logging
from datetime import datetime
from database import Session, Conversation
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS').split(',')] if os.getenv('ADMIN_IDS') else []

# States for conversation handler
MENU, RESPONDING = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f"مرحباً {user.first_name}!\n\n"
        "أنا بوت الدعم الفني. كيف يمكنني مساعدتك اليوم؟",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "للحصول على الدعم، ما عليك سوى كتابة رسالتك وسأقوم بالرد عليك في أقرب وقت ممكن."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages from users."""
    user = update.effective_user
    message = update.message.text
    
    # Save the incoming message to database
    session = Session()
    conversation = Conversation(
        chat_id=update.effective_chat.id,
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        message=message,
        response=None
    )
    session.add(conversation)
    session.commit()
    
    # Default response
    response = "شكراً لتواصلك معنا. تم استلام رسالتك وسيتم الرد عليك في أقرب وقت ممكن."
    
    # Save the response to database
    conversation.response = response
    session.commit()
    session.close()
    
    await update.message.reply_text(response)

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin menu if user is admin."""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("ليس لديك صلاحية الدخول إلى هذه القائمة.")
        return
    
    keyboard = [
        ["عرض المحادثات الأخيرة"],
        ["الرد على عميل"],
        ["إحصاءات"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    
    await update.message.reply_text(
        "مرحباً بك في لوحة التحكم للإدارة:",
        reply_markup=reply_markup
    )
    
    return MENU

async def show_recent_conversations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent conversations to admin."""
    session = Session()
    conversations = session.query(Conversation).order_by(Conversation.timestamp.desc()).limit(10).all()
    session.close()
    
    if not conversations:
        await update.message.reply_text("لا توجد محادثات مسجلة بعد.")
        return
    
    response = "آخر 10 محادثات:\n\n"
    for conv in conversations:
        response += (
            f"👤 {conv.first_name or 'Unknown'} (@{conv.username or 'N/A'})\n"
            f"🕒 {conv.timestamp.strftime('%Y-%m-%d %H:%M')}\n"
            f"📩: {conv.message}\n"
            f"📨: {conv.response or 'لم يتم الرد بعد'}\n\n"
        )
    
    await update.message.reply_text(response)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error('حدث خطأ أثناء معالجة التحديث "%s"', update, exc_info=context.error)
    
    try:
        await update.message.reply_text(
            "عذراً، حدث خطأ ما. يرجى المحاولة مرة أخرى لاحقاً."
        )
    except:
        pass

def main():
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_menu))
    
    # Add conversation handler for admin panel
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_menu)],
        states={
            MENU: [
                MessageHandler(filters.Regex("^عرض المحادثات الأخيرة$"), show_recent_conversations),
                MessageHandler(filters.Regex("^الرد على عميل$"), admin_menu),
                MessageHandler(filters.Regex("^إحصاءات$"), admin_menu),
            ],
            RESPONDING: [
                # Add handlers for responding to customers
            ],
        },
        fallbacks=[CommandHandler('admin', admin_menu)],
    )
    application.add_handler(conv_handler)
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
