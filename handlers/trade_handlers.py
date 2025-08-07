from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from ai_engine.decision_maker import DecisionMaker
from core.trade_executor import TradeExecutor
from db.crud import create_trade_record, get_user_trades
from utils.logger import logger
from notifications.telegram_notifier import send_notification
from menus.investment_menu import show_investment_menu
import asyncio

async def show_opportunities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        await update.callback_query.answer()
        
        # عرض رسالة الانتظار
        wait_msg = await update.callback_query.edit_message_text(
            "🔍 جاري البحث عن أفضل فرص المراجحة...",
            reply_markup=None
        )
        
        # الحصول على الفرص
        decision_maker = context.bot_data['decision_maker']
        opportunities = await decision_maker.get_top_opportunities(
            symbols=['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT'],
            min_profit=0.015,
            max_risk=0.3
        )
        
        if not opportunities:
            await wait_msg.edit_text("⚠️ لا توجد فرص مراجحة مناسبة حالياً. يرجى المحاولة لاحقاً.")
            return
        
        # عرض الفرص
        keyboard = []
        for idx, opp in enumerate(opportunities[:5], start=1):
            keyboard.append([
                InlineKeyboardButton(
                    text=f"فرصة #{idx} - {opp['symbol']} - ربح: {opp['profit_percentage']:.2f}%",
                    callback_data=f"select_opp_{idx}"
                )
            ])
            context.user_data[f"opp_{idx}"] = opp
        
        keyboard.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")])
        
        await wait_msg.edit_text(
            "📊 أفضل 5 فرص مراجحة متاحة الآن:\n\n"
            "💡 اختر فرصة لبدء الاستثمار",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error in show_opportunities: {str(e)}")
        await update.callback_query.edit_message_text("حدث خطأ أثناء جلب الفرص. يرجى المحاولة لاحقاً.")

async def select_opportunity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        opp_idx = int(query.data.split("_")[-1])
        opportunity = context.user_data.get(f"opp_{opp_idx}")
        
        if not opportunity:
            await query.edit_message_text("❌ انتهت صلاحية الفرصة المحددة. يرجى اختيار فرصة أخرى.")
            return
        
        context.user_data['current_opportunity'] = opportunity
        
        await query.edit_message_text(
            f"📌 الفرصة المحددة:\n\n"
            f"📊 الرمز: {opportunity['symbol']}\n"
            f"🏪 الشراء من: {opportunity['buy_from']}\n"
            f"💰 سعر الشراء: {opportunity['buy_price']:.6f}\n"
            f"🏪 البيع في: {opportunity['sell_to']}\n"
            f"💵 سعر البيع: {opportunity['sell_price']:.6f}\n"
            f"🎯 الربح المتوقع: {opportunity['profit_percentage']:.2f}%\n"
            f"⚠️ تقييم المخاطر: {opportunity['risk_score']:.1f}/1.0\n\n"
            f"💸 يرجى إدخال المبلغ الذي ترغب في استثماره (بـ USDT):",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_opportunities")]
            ])
        )
        
    except Exception as e:
        logger.error(f"Error in select_opportunity: {str(e)}")
        await update.callback_query.edit_message_text("حدث خطأ أثناء اختيار الفرصة. يرجى المحاولة لاحقاً.")

async def process_investment_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        settings = await context.bot_data['db_session'].execute(
            "SELECT min_trade_amount FROM system_settings LIMIT 1"
        )
        min_amount = settings.scalar() or 1.0
        
        if amount < min_amount:
            await update.message.reply_text(
                f"❌ المبلغ المدخل أقل من الحد الأدنى للاستثمار ({min_amount} USDT)."
            )
            return
        
        opportunity = context.user_data.get('current_opportunity')
        if not opportunity:
            await update.message.reply_text("❌ انتهت صلاحية الفرصة. يرجى البدء من جديد.")
            return
        
        # تأكيد الصفقة
        keyboard = [
            [
                InlineKeyboardButton(text="✅ تأكيد الاستثمار", callback_data="confirm_trade"),
                InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel_trade")
            ]
        ]
        
        await update.message.reply_text(
            f"⚠️ تأكيد طلب الاستثمار\n\n"
            f"📊 الرمز: {opportunity['symbol']}\n"
            f"💸 المبلغ: {amount:.2f} USDT\n"
            f"🎯 الربح المتوقع: ~{(amount * opportunity['profit_percentage'] / 100):.2f} USDT\n\n"
            f"هل تريد المتابعة؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال رقم صحيح للمبلغ المراد استثماره.")
    except Exception as e:
        logger.error(f"Error in process_investment_amount: {str(e)}")
        await update.message.reply_text("حدث خطأ أثناء معالجة المبلغ. يرجى المحاولة لاحقاً.")

async def execute_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        opportunity = context.user_data.get('current_opportunity')
        amount = float(context.user_data.get('investment_amount', 0))
        
        if not opportunity or amount <= 0:
            await query.edit_message_text("❌ بيانات الصفقة غير صالحة. يرجى البدء من جديد.")
            return
        
        # تنفيذ الصفقة
        trade_executor = context.bot_data['trade_executor']
        result = await trade_executor.execute_arbitrage(
            opportunity=opportunity,
            user_id=user.id,
            amount=amount
        )
        
        if result['status'] == 'success':
            await query.edit_message_text(
                f"✅ تم تنفيذ الصفقة بنجاح!\n\n"
                f"🆔 رقم الصفقة: {result['trade_id']}\n"
                f"💰 الربح المحقق: {result['profit']:.2f} USDT\n"
                f"⚖️ عمولة النظام: {result['commission']:.2f} USDT\n\n"
                f"يمكنك متابعة جميع صفقاتك من خلال قائمة 'سجل الصفقات'."
            )
        else:
            await query.edit_message_text("❌ فشل في تنفيذ الصفقة. يرجى المحاولة لاحقاً.")
        
    except Exception as e:
        logger.error(f"Error in execute_trade: {str(e)}")
        await update.callback_query.edit_message_text("حدث خطأ أثناء تنفيذ الصفقة. يرجى المحاولة لاحقاً.")

def setup_trade_handlers(application):
    application.add_handler(CallbackQueryHandler(show_opportunities, pattern="^show_opportunities$"))
    application.add_handler(CallbackQueryHandler(select_opportunity, pattern="^select_opp_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_investment_amount))
    application.add_handler(CallbackQueryHandler(execute_trade, pattern="^confirm_trade$"))
    application.add_handler(CallbackQueryHandler(show_investment_menu, pattern="^cancel_trade$"))
    application.add_handler(CallbackQueryHandler(show_investment_menu, pattern="^back_to_opportunities$"))
