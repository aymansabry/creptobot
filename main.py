# main.py
import logging
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import database
import handlers
import utils

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is required in .env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# on any message, update last active and route text based on state
async def text_router(update, context):
    uid = update.effective_user.id
    database.update_last_active(uid)
    st = handlers.user_states.get(uid, {})
    state = st.get("state")
    text = update.message.text.strip()

    # entering API key / secret steps
    if state == "entering_api_key":
        meta = st.get("meta",{})
        platform = meta.get("platform")
        # save the api key in meta then ask for secret
        meta["api_key"] = text
        meta["step"] = "api_secret"
        handlers.set_state(uid, "entering_api_key", meta)
        await update.message.reply_text(f"تم تسجيل API Key. الآن أرسل الـ Secret Key لـ {platform}:")
        return

    if state == "entering_api_key" and st.get("meta",{}).get("step") == "api_secret":
        meta = st.get("meta",{})
        api_key = meta.get("api_key")
        api_secret = text
        platform = meta.get("platform")
        # for kucoin we may need passphrase; ask if kucoin
        if platform.lower() == "kucoin":
            meta["api_secret"] = api_secret
            meta["step"] = "passphrase"
            handlers.set_state(uid, "entering_api_key", meta)
            await update.message.reply_text("أرسل الآن الـ Passphrase (كلمة المرور) لحساب KuCoin:")
            return
        # otherwise validate and save
        ok, msg = await utils.validate_platform_keys(platform, api_key, api_secret, None)
        if ok:
            database.add_or_update_platform(uid, platform, api_key, api_secret, None)
            await update.message.reply_text(f"✅ تم حفظ مفاتيح {platform} بنجاح.")
            handlers.clear_state(uid)
        else:
            await update.message.reply_text(f"❌ فشل التحقق من المفاتيح: {msg}\nأعد المحاولة أو اضغط إلغاء.")
        return

    if state == "entering_api_key" and st.get("meta",{}).get("step") == "passphrase":
        meta = st.get("meta",{})
        api_key = meta.get("api_key")
        api_secret = meta.get("api_secret")
        passphrase = text
        platform = meta.get("platform")
        ok, msg = await utils.validate_platform_keys(platform, api_key, api_secret, passphrase)
        if ok:
            database.add_or_update_platform(uid, platform, api_key, api_secret, passphrase)
            await update.message.reply_text(f"✅ تم حفظ مفاتيح {platform} بنجاح.")
            handlers.clear_state(uid)
        else:
            await update.message.reply_text(f"❌ فشل التحقق من المفاتيح: {msg}\nأعد المحاولة أو اضغط إلغاء.")
        return

    # wallet set
    if state == "enter_wallet":
        try:
            val = float(text)
            database.set_user_balance(uid, val)
            await update.message.reply_text(f"✅ تم تحديث رصيد محفظتك: {val:.2f} USD")
            handlers.clear_state(uid)
        except Exception:
            await update.message.reply_text("الرجاء إدخال رقم صالح للرصد.")
        return

    # entering invest amount (virtual or real)
    if state == "enter_invest_amount":
        try:
            amount = float(text)
        except:
            await update.message.reply_text("الرجاء إدخال رقم صالح للمبلغ.")
            return
        meta = st.get("meta", {})
        inv_type = meta.get("type", "virtual")
        # proceed
        await update.message.reply_text(f"تم تعيين المبلغ: {amount:.2f} USD\nجاري مراجعة المنصات...")
        plats = database.get_platforms(uid)
        if not plats:
            await update.message.reply_text("⚠️ لم تقم بإضافة منصات تداول بعد. أضف منصة أولاً من إعدادات التداول.")
            handlers.clear_state(uid)
            return
        # if virtual -> simulate
        if inv_type == "virtual":
            await update.message.reply_text("ℹ️ تنبيه: الاستثمار الوهمي عرض لمحاكاة ما يحدث بالفعلي بدون أموال حقيقية.")
            res = await utils.simulate_virtual_trade(amount, symbol="BTC/USDT")
            # log
            database.log_investment(uid, "binance", "virtual", amount, res["symbol"], res["symbol"],
                                    res["buy_price"], res["sell_price"], res["gross_profit"], res["net_profit"])
            await update.message.reply_text(f"📊 جاري تنفيذ شراء عملة {res['symbol']} بسعر {res['buy_price']:.2f} USD...")
            await asyncio.sleep(1)
            await update.message.reply_text(f"📉 جاري تنفيذ بيع عملة {res['symbol']} بسعر {res['sell_price']:.2f} USD...")
            await asyncio.sleep(1)
            await update.message.reply_text(f"✅ تمت العملية بنجاح! أرباحك المتوقعة صافية: {res['net_profit']:.2f} USD (بعد خصم نسبة البوت)")
            handlers.clear_state(uid)
            return
        else:
            # real invest (but maybe simulated depending on ALLOW_REAL_TRADES)
            # choose first enabled platform
            platform_entry = None
            for p in plats:
                if p.get("enabled"):
                    platform_entry = p
                    break
            if not platform_entry:
                await update.message.reply_text("لا توجد منصات مفعّلة، رجاء تفعيل منصة أولاً.")
                handlers.clear_state(uid)
                return
            await update.message.reply_text("ℹ️ جاري تنفيذ العملية الحقيقية (أو محاكاتها اعتمادًا على إعداد السيرفر)...")
            res = await utils.execute_real_trade(platform_entry, amount, symbol="BTC/USDT")
            if not res.get("ok"):
                await update.message.reply_text(f"❌ فشل التنفيذ: {res.get('msg')}")
                handlers.clear_state(uid)
                return
            database.log_investment(uid, platform_entry["platform_name"], "real", amount, "BTC/USDT", "BTC/USDT",
                                    res.get("buy_price"), res.get("sell_price"), res.get("gross_profit"), res.get("net_profit"))
            # if not simulated deduct balance
            if not res.get("simulated"):
                bal = database.get_user_balance(uid)
                database.set_user_balance(uid, max(0, bal - amount))
            await update.message.reply_text(f"✅ تمت العملية. الربح الصافي: {res.get('net_profit'):.2f} USD ({'محاكاة' if res.get('simulated') else 'حقيقية'})")
            handlers.clear_state(uid)
            return

    # default fallback - if none handled
    await update.message.reply_text("استخدم /start للعودة إلى القائمة الرئيسية.")

def register_handlers(app):
    app.add_handler(CommandHandler("start", handlers.start_cmd))
    app.add_handler(CallbackQueryHandler(handlers.callback_router))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_router))
