from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from db.models import User

def admin_dashboard(update, context):
    buttons = [
        [InlineKeyboardButton("🔄 تحديث الإحصائيات", callback_data='refresh_stats')],
        [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data='manage_users')],
        [InlineKeyboardButton("💼 المحفظة المركزية", callback_data='central_wallet')]
    ]
    
    users_count = User.query.count()
    update.message.reply_text(
        f"لوحة التحكم الإدارية\nالمستخدمون النشطون: {users_count}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
