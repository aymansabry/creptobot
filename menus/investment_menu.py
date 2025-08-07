from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ai_engine.decision_maker import DecisionMaker

async def show_investment_menu(update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 عرض الفرص الحالية", callback_data="show_opportunities")],
        [InlineKeyboardButton("🔄 استثمار آلي مستمر", callback_data="continuous_investment")],
        [InlineKeyboardButton("📊 أداء الاستثمار", callback_data="investment_performance")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
    ]
    
    await update.callback_query.edit_message_text(
        "📈 قائمة الاستثمار:\n\n"
        "اختر الخيار المناسب لك:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_continuous_investment_menu(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    investment = await context.bot_data['db_session'].execute(
        f"SELECT * FROM continuous_investments WHERE user_id = {user.id} LIMIT 1"
    )
    investment = investment.fetchone()
    
    if investment and investment.is_active:
        status_text = "🟢 نشط"
        action_button = InlineKeyboardButton("⛔ إيقاف الاستثمار", callback_data="stop_continuous")
    else:
        status_text = "🔴 غير نشط"
        action_button = InlineKeyboardButton("✅ تفعيل الاستثمار", callback_data="start_continuous")
    
    text = (
        "🔄 الاستثمار الآلي المستمر:\n\n"
        f"الحالة الحالية: {status_text}\n\n"
    )
    
    if investment:
        text += (
            f"💸 المبلغ المخصص: {investment.amount} USDT\n"
            f"🎯 الحد الأدنى للربح: {investment.min_profit_percentage}%\n"
            f"📅 آخر تحديث: {investment.updated_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        )
    
    text += "مع هذا الخيار، سيقوم النظام تلقائياً باستثمار الأموال في أفضل الفرص التي تتجاوز الحد الأدنى للربح الذي تحدده."
    
    keyboard = [
        [action_button],
        [InlineKeyboardButton("✏️ تعديل الإعدادات", callback_data="edit_continuous")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_investment")]
    ]
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def setup_continuous_investment(update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "📝 إعداد الاستثمار المستمر:\n\n"
        "يرجى إرسال المبلغ الذي ترغب في تخصيصه للاستثمار الآلي (بالـ USDT):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_continuous_setup")]
        ])
    )

async def process_continuous_amount(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        context.user_data['continuous_amount'] = amount
        
        await update.message.reply_text(
            "🎯 الآن، يرجى تحديد الحد الأدنى لنسبة الربح المطلوبة (مثال: 1.5 لـ 1.5%):",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_continuous_setup")]
            ])
        )
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال رقم صحيح للمبلغ.")

async def process_continuous_profit(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        min_profit = float(update.message.text)
        amount = context.user_data.get('continuous_amount')
        
        if not amount or amount <= 0:
            await update.message.reply_text("❌ بيانات غير صالحة. يرجى البدء من جديد.")
            return
        
        # حفظ الإعدادات
        user = update.effective_user
        await context.bot_data['db_session'].execute(
            f"""
            INSERT INTO continuous_investments (user_id, amount, min_profit_percentage, is_active)
            VALUES ({user.id}, {amount}, {min_profit}, 1)
            ON CONFLICT (user_id) DO UPDATE 
            SET amount = {amount}, min_profit_percentage = {min_profit}, is_active = 1
            """
        )
        await context.bot_data['db_session'].commit()
        
        await update.message.reply_text(
            f"✅ تم إعداد الاستثمار الآلي بنجاح!\n\n"
            f"💸 المبلغ المخصص: {amount} USDT\n"
            f"🎯 الحد الأدنى للربح: {min_profit}%\n\n"
            f"سيبدأ النظام الآن في استثمار الأموال تلقائياً عند توفر فرص مناسبة."
        )
        
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال نسبة ربح صحيحة.")
    except Exception as e:
        await update.message.reply_text("❌ حدث خطأ أثناء حفظ الإعدادات. يرجى المحاولة لاحقاً.")

async def stop_continuous_investment(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await context.bot_data['db_session'].execute(
        f"UPDATE continuous_investments SET is_active = 0 WHERE user_id = {user.id}"
    )
    await context.bot_data['db_session'].commit()
    
    await update.callback_query.edit_message_text(
        "⛔ تم إيقاف الاستثمار الآلي المستمر.\n\n"
        "سيتم إكمال أي صفقات جارية ثم إيقاف الاستثمارات الجديدة.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_continuous")]
        ])
    )
