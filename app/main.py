from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import random, os

# إعدادات البيئة
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_COMMISSION = float(os.getenv("BOT_COMMISSION", 0.05))
OWNER_WALLET = os.getenv("OWNER_WALLET", "OWNER")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")

# قاعدة البيانات
Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    deal_code = Column(String)
    amount = Column(Float)
    profit = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# توليد صفقات ذكية
ai_deals = [
    {"code": ''.join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=6)), "expected_profit": round(random.uniform(5, 15), 2), "estimated_time": random.choice(["2 دقائق", "5 دقائق", "10 دقائق"]) }
    for _ in range(5)
]

user_investments = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🤖 هذه قائمة بأفضل الصفقات الحالية:\n"
    buttons = []
    for deal in ai_deals:
        text += f"\n🔹 كود الصفقة: {deal['code']}\n💰 نسبة الربح: {deal['expected_profit']}%\n⏱️ المدة: {deal['estimated_time']}\n"
        buttons.append([InlineKeyboardButton(f"استثمر في {deal['code']}", callback_data=deal['code'])])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    code = query.data
    context.user_data['deal_code'] = code
    await query.message.reply_text(f"💸 أدخل مبلغ الاستثمار لـ الصفقة {code} (الحد الأدنى 1 USDT):")

async def handle_investment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        amount = float(update.message.text)
        if amount < 1:
            raise ValueError("قيمة قليلة")
    except:
        await update.message.reply_text("❌ أدخل مبلغ صالح (≥ 1 USDT)")
        return

    code = context.user_data.get("deal_code")
    deal = next((d for d in ai_deals if d['code'] == code), None)
    if not deal:
        await update.message.reply_text("⚠️ الصفقة غير موجودة.")
        return

    profit_percent = deal['expected_profit']
    gross_profit = round(amount * profit_percent / 100, 2)
    commission = round(gross_profit * BOT_COMMISSION, 2)
    net_profit = gross_profit - commission

    # حفظ المعاملة
    session = Session()
    session.add(Transaction(user_id=user_id, deal_code=code, amount=amount, profit=net_profit))
    session.commit()

    # إشعار العميل
    await update.message.reply_text(
        f"✅ تم استثمار {amount} USDT في الصفقة {code}\n"
        f"💰 ربح متوقع: {gross_profit} USDT\n"
        f"🔻 خصم البوت: {commission} USDT\n"
        f"📈 صافي الربح: {net_profit} USDT\n"
        f"📬 سيتم التحويل التلقائي بعد انتهاء التنفيذ ({deal['estimated_time']})"
    )

    # إشعار المالك (مطبوع فقط الآن)
    print(f"🔔 المالك: استثمار جديد من {user_id} بمبلغ {amount} في {code}, ربح صافٍ: {net_profit}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_investment))
    app.run_polling()
    #

if __name__ == "__main__":
    main()
