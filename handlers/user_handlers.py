from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from typing import Dict, Any
from db.crud import get_user, create_user, get_user_wallet, create_wallet
from db.models import User
from utils.logger import logger
from notifications.telegram_notifier import send_notification
from menus.main_menu import show_main_menu

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        db_user = await get_user(context.bot_data['db_session'], user.id)
        
        if not db_user:
            new_user = {
                'telegram_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
            db_user = await create_user(context.bot_data['db_session'], new_user)
            
            wallet_data = {
                'user_id': db_user.id,
                'address': f"user_{user.id}_wallet",
                'balances': {'USDT': 0.0}
            }
            await create_wallet(context.bot_data['db_session'], wallet_data)
            
            await update.message.reply_text(
                "🎉 مرحباً بك في نظام التداول الآلي بالمراجحة!\n"
                "✅ تم إنشاء حسابك بنجاح.\n"
                "💰 يرجى إيداع الأموال لبدء التداول."
            )
            
            await send_notification(
                context.bot_data['admin_ids'][0],
                f"👤 مستخدم جديد انضم إلى النظام\n"
                f"🆔 ID: {user.id}\n"
                f"👤 الاسم: {user.full_name}\n"
                f"📅 التاريخ: {update.message.date}"
            )
        else:
            await update.message.reply_text(
                "👋 مرحباً بعودتك!\n"
                "✅ تم التعرف على حسابك بنجاح."
            )
        
        await show_main_menu(update, context)
        
    except Exception as e:
        logger.error(f"Error in start handler: {str(e)}")
        await update.message.reply_text("حدث خطأ أثناء معالجة طلبك. يرجى المحاولة لاحقاً.")

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        wallet = await get_user_wallet(context.bot_data['db_session'], user.id)
        
        if not wallet:
            await update.message.reply_text("❌ لم يتم العثور على محفظتك. يرجى الاتصال بالدعم.")
            return
        
        deposit_address = context.bot_data['main_wallet_address']
        await update.message.reply_text(
            f"💰 لإيداع الأموال، يرجى إرسال USDT إلى العنوان التالي:\n\n"
            f"📌 عنوان المحفظة: `{deposit_address}`\n\n"
            f"⚠️ تأكد من استخدام شبكة TRC20 (TRON) لتجنب رسوم عالية.\n"
            f"💸 بعد الإيداع، سيتم التحقق تلقائياً من المعاملة وإضافتها إلى رصيدك.",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in deposit handler: {str(e)}")
        await update.message.reply_text("حدث خطأ أثناء معالجة طلبك. يرجى المحاولة لاحقاً.")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        wallet = await get_user_wallet(context.bot_data['db_session'], user.id)
        
        if not wallet:
            await update.message.reply_text("❌ لم يتم العثور على محفظتك. يرجى الاتصال بالدعم.")
            return
        
        balance_text = "💰 رصيدك الحالي:\n\n"
        for currency, amount in wallet.balances.items():
            balance_text += f"• {currency}: {amount:.2f}\n"
        
        await update.message.reply_text(balance_text)
        
    except Exception as e:
        logger.error(f"Error in balance handler: {str(e)}")
        await update.message.reply_text("حدث خطأ أثناء معالجة طلبك. يرجى المحاولة لاحقاً.")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "❌ استخدام خاطئ للأمر. يرجى استخدام الصيغة التالية:\n"
                "/withdraw <المبلغ> <عنوان المحفظة>"
            )
            return
        
        amount = float(args[0])
        address = args[1]
        
        user = update.effective_user
        wallet = await get_user_wallet(context.bot_data['db_session'], user.id)
        
        if not wallet:
            await update.message.reply_text("❌ لم يتم العثور على محفظتك. يرجى الاتصال بالدعم.")
            return
        
        if wallet.balances.get('USDT', 0) < amount:
            await update.message.reply_text("❌ رصيدك غير كافي لهذا السحب.")
            return
        
        await context.bot_data['exchange_api'].withdraw(
            currency='USDT',
            amount=amount,
            address=address
        )
        
        wallet.balances['USDT'] -= amount
        await context.bot_data['db_session'].commit()
        
        await update.message.reply_text(
            f"✅ تم تنفيذ طلب السحب بنجاح\n\n"
            f"💸 المبلغ: {amount:.2f} USDT\n"
            f"📌 العنوان: {address}\n\n"
            f"🔄 قد تستغرق المعاملة بعض الوقت لتظهر في محفظتك."
        )
        
    except Exception as e:
        logger.error(f"Error in withdraw handler: {str(e)}")
        await update.message.reply_text("حدث خطأ أثناء معالجة طلبك. يرجى المحاولة لاحقاً.")

def setup_user_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("deposit", deposit))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("withdraw", withdraw))
