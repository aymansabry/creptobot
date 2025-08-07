# handlers/admin_handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from typing import Dict, Any
from db.crud import get_user, get_user_trades, get_system_settings, update_system_settings
from utils.logger import logger
import re

async def check_admin_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دالة مساعدة للتحقق من صلاحيات الأدمن"""
    user = update.effective_user
    if not user:
        return False
    
    db_session = context.bot_data['db_session']
    admin_ids = context.bot_data.get('admin_ids', [])
    
    # التحقق من أن المستخدم موجود في قائمة الأدمن
    if user.id in admin_ids:
        return True
    
    # أو التحقق من قاعدة البيانات إذا كان is_admin = 1
    db_user = await get_user(db_session, user.id)
    if db_user and getattr(db_user, 'is_admin', 0) == 1:
        return True
    
    return False

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await check_admin_access(update, context):
            await update.message.reply_text("❌ ليس لديك صلاحية الوصول إلى هذه الأداة.")
            return
        
        db_session = context.bot_data['db_session']
        
        # جلب الإحصائيات
        total_users = await db_session.execute("SELECT COUNT(*) FROM users")
        total_trades = await db_session.execute("SELECT COUNT(*) FROM trades")
        total_profit = await db_session.execute("SELECT SUM(profit) FROM trades WHERE status='completed'")
        total_commission = await db_session.execute("SELECT SUM(commission) FROM trades")
        
        stats_text = (
            "📊 إحصائيات النظام:\n\n"
            f"👥 عدد المستخدمين: {total_users.scalar()}\n"
            f"🔄 عدد الصفقات: {total_trades.scalar()}\n"
            f"💰 إجمالي الأرباح: {total_profit.scalar() or 0:.2f} USDT\n"
            f"⚖️ إجمالي العمولات: {total_commission.scalar() or 0:.2f} USDT\n\n"
            f"🛠️ أدوات المدير:"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث إعدادات النظام", callback_data="update_settings")],
            [InlineKeyboardButton("📤 سحب الأرباح", callback_data="withdraw_profits")],
            [InlineKeyboardButton("📩 إرسال إشعار عام", callback_data="broadcast_message")]
        ]
        
        await update.message.reply_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
            
    except Exception as e:
        logger.error(f"Error in admin_stats: {str(e)}")
        await update.message.reply_text("حدث خطأ أثناء جلب الإحصائيات. يرجى المحاولة لاحقاً.")

async def update_system_settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await check_admin_access(update, context):
            await update.answer("❌ ليس لديك صلاحية الوصول إلى هذه الأداة.", show_alert=True)
            return
            
        query = update.callback_query
        await query.answer()
        
        settings = await get_system_settings(context.bot_data['db_session'])
        
        await query.edit_message_text(
            "⚙️ إعدادات النظام الحالية:\n\n"
            f"💸 الحد الأدنى للصفقة: {settings.min_trade_amount} USDT\n"
            f"⚖️ عمولة البوت: {settings.bot_commission * 100}%\n"
            f"⚠️ حد المخاطرة: {settings.risk_threshold * 100}%\n\n"
            "يرجى إرسال الإعدادات الجديدة بالصيغة التالية:\n"
            "/update_settings min_trade=10 commission=0.1 risk=0.3"
        )
        
    except Exception as e:
        logger.error(f"Error in update_system_settings_handler: {str(e)}")
        await query.edit_message_text("حدث خطأ أثناء معالجة الطلب. يرجى المحاولة لاحقاً.")

async def process_settings_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await check_admin_access(update, context):
            await update.message.reply_text("❌ ليس لديك صلاحية تعديل الإعدادات.")
            return
        
        args = ' '.join(context.args).lower()
        updates = {}
        
        min_trade_match = re.search(r'min_trade=(\d+\.?\d*)', args)
        if min_trade_match:
            updates['min_trade_amount'] = float(min_trade_match.group(1))
        
        commission_match = re.search(r'commission=(\d+\.?\d*)', args)
        if commission_match:
            updates['bot_commission'] = float(commission_match.group(1))
        
        risk_match = re.search(r'risk=(\d+\.?\d*)', args)
        if risk_match:
            updates['risk_threshold'] = float(risk_match.group(1))
        
        if not updates:
            await update.message.reply_text("❌ لم يتم تحديد أي إعدادات للتحديث.")
            return
        
        await update_system_settings(
            session=context.bot_data['db_session'],
            updates=updates,
            updated_by=update.effective_user.id
        )
        
        await update.message.reply_text("✅ تم تحديث إعدادات النظام بنجاح.")
        
    except Exception as e:
        logger.error(f"Error in process_settings_update: {str(e)}")
        await update.message.reply_text("حدث خطأ أثناء تحديث الإعدادات. يرجى التحقق من الصيغة والمحاولة مرة أخرى.")

def setup_admin_handlers(application):
    application.add_handler(CommandHandler("admin", admin_stats))
    application.add_handler(CallbackQueryHandler(update_system_settings_handler, pattern="^update_settings$"))
    application.add_handler(CommandHandler("update_settings", process_settings_update))