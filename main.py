# main.py
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from handlers import start, virtual_investment, set_amount, market_status

# إعداد اللوج
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# البوت الأساسي
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

app = ApplicationBuilder().token(TOKEN).build()

# أوامر
app.add_handler(CommandHandler("start", start))

# رسائل الاستثمار الوهمي
app.add_handler(MessageHandler(filters.Regex("^💰 استثمار وهمي$"), virtual_investment))
app.add_handler(MessageHandler(filters.Regex("^[0-9]+(\.[0-9]+)?$"), set_amount))

# حالة السوق
app.add_handler(MessageHandler(filters.Regex("^📊 حالة السوق$"), market_status))

# تشغيل البوت
if __name__ == "__main__":
    print("🚀 البوت شغال...")
    app.run_polling()
