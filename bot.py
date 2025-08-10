from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database import query, execute

# بدء المحادثة
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_name = update.effective_user.username or update.effective_user.first_name

    # حفظ المستخدم في قاعدة البيانات إذا لم يكن موجود
    existing = query("SELECT * FROM users WHERE user_id = %s", (user_id,))
    if not existing:
        execute("INSERT INTO users (user_id, username) VALUES (%s, %s)", (user_id, user_name))

    keyboard = [
        [InlineKeyboardButton("📊 عرض الرصيد", callback_data="balance")],
        [InlineKeyboardButton("⚙️ إعدادات API", callback_data="set_api")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        f"مرحباً {user_name} 👋\nاختر أحد الخيارات أدناه:",
        reply_markup=reply_markup
    )

# التعامل مع الأزرار
def button_handler(update: Update, context: CallbackContext):
    query_data = update.callback_query
    query_data.answer()

    if query_data.data == "balance":
        # استعلام عن الرصيد (كمثال)
        user_id = query_data.from_user.id
        balance = get_user_balance(user_id)
        query_data.edit_message_text(f"💰 رصيدك الحالي: {balance} USDT")
    elif query_data.data == "set_api":
        query_data.edit_message_text("🔑 أرسل لي الـ API Key و Secret بالشكل التالي:\n`API_KEY,API_SECRET`")

# دالة وهمية للحصول على الرصيد (تعدل لاحقاً لربط منصات التداول)
def get_user_balance(user_id):
    # مثال: نعيد قيمة ثابتة حالياً
    return 100.0
