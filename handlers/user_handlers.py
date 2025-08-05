from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from database.queries import get_user, create_user
from utils.keyboards import main_menu_keyboard
from services.market_analysis import get_investment_opportunities

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = await get_user(user.id)
    
    if not db_user:
        await create_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
    
    await update.message.reply_text(
        f"مرحباً {user.first_name}!\n\n"
        "بوت الاستثمار الآلي في العملات الرقمية عبر المراجحة الجغرافية\n"
        "اختر أحد الخيارات من القائمة:",
        reply_markup=main_menu_keyboard()
    )

async def show_investment_opportunities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    opportunities = await get_investment_opportunities(limit=5)
    
    if not opportunities:
        await update.callback_query.edit_message_text(
            "لا توجد فرص استثمارية متاحة حالياً. يرجى المحاولة لاحقاً.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    message = "🏆 أفضل 5 فرص استثمارية متاحة الآن:\n\n"
    for idx, opp in enumerate(opportunities, 1):
        message += (
            f"{idx}. {opp.base_currency} → {opp.target_currency}\n"
            f"   📌 الشراء من: {opp.buy_market}\n"
            f"   📌 البيع في: {opp.sell_market}\n"
            f"   💰 الربح المتوقع: {opp.expected_profit}%\n"
            f"   ⏳ المدة: {opp.duration_minutes} دقيقة\n\n"
        )
    
    keyboard = [
        [InlineKeyboardButton(f"استثمار في الفرصة {i+1}", callback_data=f"invest_{opp.id}")]
        for i, opp in enumerate(opportunities)
    ]
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")])
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
