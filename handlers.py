# handlers.py
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database
import utils
from datetime import datetime, timedelta

user_states = {}  # uid -> {"state": str, "meta": {}}

main_kb = InlineKeyboardMarkup([
    [InlineKeyboardButton("1️⃣ تسجيل أو تعديل بيانات التداول", callback_data="menu_manage_trading")],
    [InlineKeyboardButton("2️⃣ ابدأ استثمار", callback_data="menu_start_invest")],
    [InlineKeyboardButton("3️⃣ استثمار وهمي", callback_data="menu_virtual_invest")],
    [InlineKeyboardButton("4️⃣ كشف حساب عن فترة", callback_data="menu_account_statement")],
    [InlineKeyboardButton("5️⃣ حالة السوق", callback_data="menu_market_status")],
    [InlineKeyboardButton("6️⃣ إيقاف الاستثمار", callback_data="menu_stop_invest")],
])

manage_kb = InlineKeyboardMarkup([
    [InlineKeyboardButton("➕ إضافة منصة", callback_data="trade_add_platform")],
    [InlineKeyboardButton("✏️ تعديل/عرض المنصات", callback_data="trade_list_platforms")],
    [InlineKeyboardButton("🏦 محفظة المستخدم (الرصيد)", callback_data="trade_wallet")],
    [InlineKeyboardButton("🔙 رجوع", callback_data="menu_main")],
])

def set_state(uid, state, meta=None):
    user_states[uid] = {"state": state, "meta": meta or {}}

def clear_state(uid):
    if uid in user_states:
        del user_states[uid]

# /start
async def start_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    database.ensure_user(uid)
    database.update_last_active(uid)
    await update.message.reply_text("مرحبًا! اختر من القائمة:", reply_markup=main_kb)

# central callback router
async def callback_router(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data
    database.update_last_active(uid)

    # MAIN
    if data == "menu_main":
        await query.edit_message_text("القائمة الرئيسية:", reply_markup=main_kb)
        clear_state(uid)
        return

    if data == "menu_manage_trading":
        await query.edit_message_text("تسجيل أو تعديل بيانات التداول — اختر:", reply_markup=manage_kb)
        clear_state(uid)
        return

    # add platform flow
    if data == "trade_add_platform":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Binance", callback_data="addplat:Binance")],
            [InlineKeyboardButton("KuCoin", callback_data="addplat:KuCoin")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="menu_manage_trading")]
        ])
        await query.edit_message_text("اختر المنصة:", reply_markup=kb)
        return

    if data.startswith("addplat:"):
        platform = data.split(":",1)[1]
        set_state(uid, "enter_api_key", {"platform": platform, "step": "api_key"})
        await query.edit_message_text(f"أرسل الآن API Key لـ {platform} (أرسل النص فقط):")
        return

    if data == "trade_list_platforms":
        plats = database.get_platforms(uid)
        if not plats:
            await query.edit_message_text("لا توجد منصات مضافة بعد.")
            return
        text = ""
        buttons = []
        for p in plats:
            status = "✅ مفعل" if p.get("enabled") else "🔴 موقوف"
            sandbox = " (sandbox)" if p.get("is_sandbox") else ""
            text += f"- {p['platform_name']}{sandbox}: {status}\n"
            buttons.append([InlineKeyboardButton(f"تعديل {p['platform_name']}", callback_data=f"editplat:{p['platform_name']}"),
                            InlineKeyboardButton("إيقاف/تفعيل", callback_data=f"toggleplat:{p['platform_name']}")])
        buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_manage_trading")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data.startswith("editplat:"):
        platform = data.split(":",1)[1]
        set_state(uid, "enter_api_key", {"platform": platform, "step": "api_key", "editing": True})
        await query.edit_message_text(f"أرسل API Key جديد لـ {platform}:")
        return

    if data.startswith("toggleplat:"):
        platform = data.split(":",1)[1]
        p = database.get_platform_by_name(uid, platform)
        if not p:
            await query.edit_message_text("المنصة غير موجودة.")
            return
        new = not bool(p.get("enabled"))
        database.set_platform_enabled(uid, platform, new)
        await query.edit_message_text(f"تم {'تفعيل' if new else 'إيقاف'} منصة {platform}.")
        return

    if data == "trade_wallet":
        bal = database.get_user_balance(uid)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 تعيين/تحديث الرصيد", callback_data="wallet_set")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="menu_manage_trading")]
        ])
        await query.edit_message_text(f"رصيدك الحالي: {bal:.2f} USD", reply_markup=kb)
        return

    if data == "wallet_set":
        set_state(uid, "enter_wallet")
        await query.edit_message_text("أرسل الآن رصيد محفظتك (رقم بالدولار):")
        return

    # account statement date picker
    if data == "menu_account_statement":
        today = datetime.utcnow().date()
        rows = []
        for i in range(7):
            d = today - timedelta(days=i)
            s = d.strftime("%Y-%m-%d")
            rows.append([InlineKeyboardButton(s, callback_data=f"stmt:{s}")])
        rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_main")])
        await query.edit_message_text("اختر بداية الفترة:", reply_markup=InlineKeyboardMarkup(rows))
        return

    if data.startswith("stmt:"):
        start_date = data.split(":",1)[1]
        total = database.get_investments_sum_since(uid, start_date)
        await query.edit_message_text(f"إجمالي الأرباح منذ {start_date}: {total:.2f} USD")
        return

    # start invest (real)
    if data == "menu_start_invest":
        set_state(uid, "choose_invest_amount", {"type":"real"})
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 استخدام رصيد المحفظة", callback_data="invest_use_wallet")],
            [InlineKeyboardButton("✏️ إدخال مبلغ جديد", callback_data="invest_enter_amount")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="menu_main")]
        ])
        await query.edit_message_text("اختر طريقة تحديد المبلغ:", reply_markup=kb)
        return

    if data == "invest_use_wallet":
        bal = database.get_user_balance(uid)
        if bal <= 0:
            await query.edit_message_text("رصيدك لا يكفي للاستثمار. الرجاء إيداع رصيد أولاً.")
            clear_state(uid)
            return
        set_state(uid, "confirm_invest", {"amount": bal, "type": "real"})
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("نعم ابدأ الآن", callback_data="confirm_invest_yes")],
            [InlineKeyboardButton("لا، إلغاء", callback_data="menu_main")]
        ])
        await query.edit_message_text(f"هل تريد استخدام رصيدك {bal:.2f} USD لبدء الاستثمار؟", reply_markup=kb)
        return

    if data == "invest_enter_amount":
        set_state(uid, "enter_invest_amount", {"type":"real"})
        await query.edit_message_text("أرسل مبلغ الاستثمار (USD):")
        return

    if data == "confirm_invest_yes":
        st = user_states.get(uid)
        if not st or st.get("state") != "confirm_invest":
            await query.edit_message_text("لا توجد عملية للتأكيد.")
            return
        amount = float(st["meta"]["amount"])
        plats = database.get_platforms(uid)
        if not plats:
            await query.edit_message_text("⚠️ أضف منصات تداول أولاً.")
            clear_state(uid)
            return
        # choose first enabled platform
        platform_entry = None
        for p in plats:
            if p.get("enabled"):
                platform_entry = p
                break
        if not platform_entry:
            await query.edit_message_text("لا توجد منصات مفعّلة.")
            clear_state(uid)
            return
        await query.edit_message_text("جاري تنفيذ الصفقة، قد تكون محاكاة وفق إعدادات الخادم...")
        res = await utils.execute_real_trade(platform_entry, amount, symbol="BTC/USDT")
        if not res.get("ok"):
            await query.edit_message_text(f"فشل التنفيذ: {res.get('msg')}")
            clear_state(uid)
            return
        database.log_investment(uid, platform_entry["platform_name"], "real", amount, "BTC/USDT", "BTC/USDT",
                                res.get("buy_price"), res.get("sell_price"), res.get("gross_profit"), res.get("net_profit"))
        if not res.get("simulated"):
            bal = database.get_user_balance(uid)
            database.set_user_balance(uid, max(0, bal - amount))
        await query.edit_message_text(
            f"✅ تمت العملية.\nالربح الصافي: {res.get('net_profit'):.2f} USD\n({ 'محاكاة' if res.get('simulated') else 'حقيقية'})"
        )
        clear_state(uid)
        return

    # virtual invest entry
    if data == "menu_virtual_invest":
        set_state(uid, "enter_invest_amount", {"type":"virtual"})
        await query.edit_message_text("الاستثمار الوهمي — الرجاء إدخال مبلغ الاستثمار (USD):")
        return

    # market status
    if data == "menu_market_status":
        await query.edit_message_text("جاري تجميع تحليل السوق...")
        try:
            coins = ["BTC/USDT","ETH/USDT","BNB/USDT"]
            binance = __import__('ccxt').binance()
            tickers = await utils.to_thread(binance.fetch_tickers)
            prices = ""
            for c in coins:
                if c in tickers:
                    prices += f"{c}: {tickers[c]['last']:.2f} USD\n"
        except Exception:
            prices = "تعذر جلب الأسعار حالياً."
        prompt = f"قدم تحليل للسوق ونصائح استثمارية. الأسعار الحالية:\n{prices}"
        try:
            resp = await utils.to_thread(__import__('openai').ChatCompletion.create,
                                        model="gpt-4o-mini",
                                        messages=[{"role":"system","content":"أنت مساعد خبير في تداول العملات الرقمية."},
                                                  {"role":"user","content":prompt}],
                                        max_tokens=400, temperature=0.7)
            if isinstance(resp, dict):
                analysis = resp.get("choices",[{}])[0].get("message",{}).get("content","")
            else:
                analysis = resp.choices[0].message.content
        except Exception as e:
            analysis = f"تعذر توليد تحليل كامل: {e}"
        full = analysis + "\n\n" + prices
        parts = [full[i:i+3800] for i in range(0,len(full),3800)]
        for p in parts:
            await query.message.reply_text(p)
        return

    if data == "menu_stop_invest":
        database.set_user_investing(uid, False)
        await query.edit_message_text("تم إيقاف الاستثمار لحسابك. لن يتم استخدام أموالك حتى تُفعل مجددًا.")
        return

    # fallback
    await query.edit_message_text("أمر غير معروف.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة", callback_data="menu_main")]]))

# text router for inputs while in state
async def text_router(update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    st = user_states.get(uid, {})
    state = st.get("state")
    database.update_last_active(uid)

    if state == "enter_api_key":
        meta = st.get("meta",{})
        platform = meta.get("platform")
        meta["api_key"] = text
        meta["step"] = "api_secret"
        set_state(uid, "enter_api_key", meta)
        await update.message.reply_text("تم حفظ الـ API Key مؤقتًا. الآن أرسل Secret Key:")
        return

    if state == "enter_api_key" and st.get("meta",{}).get("step") == "api_secret":
        meta = st.get("meta",{})
        api_key = meta.get("api_key")
        api_secret = text
        platform = meta.get("platform")
        # if kucoin ask passphrase
        if platform.lower() == "kucoin":
            meta["api_secret"] = api_secret
            meta["step"] = "passphrase"
            set_state(uid, "enter_api_key", meta)
            await update.message.reply_text("أرسل الآن Passphrase (Passphrase) لحساب KuCoin:")
            return
        ok, msg = await utils.validate_platform_keys(platform, api_key, api_secret, None, use_sandbox=False)
        if ok:
            database.add_or_update_platform(uid, platform, api_key, api_secret, None)
            await update.message.reply_text("✅ ✅ تم التحقق من المفاتيح وحفظها بنجاح.")
            clear_state(uid)
        else:
            await update.message.reply_text(f"❌ فشل التحقق: {msg}\nأعد المحاولة أو اضغط إلغاء.")
        return

    if state == "enter_api_key" and st.get("meta",{}).get("step") == "passphrase":
        meta = st.get("meta",{})
        api_key = meta.get("api_key")
        api_secret = meta.get("api_secret")
        passphrase = text
        platform = meta.get("platform")
        ok, msg = await utils.validate_platform_keys(platform, api_key, api_secret, passphrase, use_sandbox=False)
        if ok:
            database.add_or_update_platform(uid, platform, api_key, api_secret, passphrase)
            await update.message.reply_text("✅ ✅ تم التحقق من مفاتيح KuCoin وحفظها.")
            clear_state(uid)
        else:
            await update.message.reply_text(f"❌ فشل التحقق: {msg}\nأعد المحاولة.")
        return

    if state == "enter_wallet":
        try:
            val = float(text)
            database.set_user_balance(uid, val)
            await update.message.reply_text(f"✅ تم تحديث رصيد محفظتك: {val:.2f} USD")
            clear_state(uid)
        except:
            await update.message.reply_text("الرجاء إدخال رقم صالح.")
        return

    if state == "enter_invest_amount":
        try:
            amount = float(text)
        except:
            await update.message.reply_text("الرجاء إدخال رقم صالح.")
            return
        meta = st.get("meta",{})
        inv_type = meta.get("type","virtual")
        await update.message.reply_text(f"تم تعيين المبلغ: {amount:.2f} USD\nجاري مراجعة المنصات...")
        plats = database.get_platforms(uid)
        if not plats:
            await update.message.reply_text("⚠️ لا توجد منصات مضافة. أضف منصة أولًا.")
            clear_state(uid)
            return
        if inv_type == "virtual":
            await update.message.reply_text("ℹ️ ملاحظة: هذا استثمار وهمي—لا تستخدم أموال حقيقية.")
            res = await utils.simulate_virtual_trade(amount, symbol="BTC/USDT")
            database.log_investment(uid, "binance", "virtual", amount, res["symbol"], res["symbol"], res["buy_price"], res["sell_price"], res["gross_profit"], res["net_profit"])
            await update.message.reply_text(f"📊 جاري شراء {res['symbol']} بسعر {res['buy_price']:.2f} USD...")
            await asyncio.sleep(1)
            await update.message.reply_text(f"📉 جاري بيع {res['symbol']} بسعر {res['sell_price']:.2f} USD...")
            await asyncio.sleep(1)
            await update.message.reply_text(f"✅ تمت العملية بنجاح! أرباحك المتوقعة (صافية): {res['net_profit']:.2f} USD")
            clear_state(uid)
            return
        else:
            # real invest
            platform_entry = None
            for p in plats:
                if p.get("enabled"):
                    platform_entry = p
                    break
            if not platform_entry:
                await update.message.reply_text("لا توجد منصات مفعلة.")
                clear_state(uid)
                return
            await update.message.reply_text("ℹ️ جاري تنفيذ الاستثمار (حقيقي أو محاكاة اعتمادًا على إعداد الخادم)...")
            res = await utils.execute_real_trade(platform_entry, amount, symbol="BTC/USDT")
            if not res.get("ok"):
                await update.message.reply_text(f"فشل التنفيذ: {res.get('msg')}")
                clear_state(uid)
                return
            database.log_investment(uid, platform_entry["platform_name"], "real", amount, "BTC/USDT", "BTC/USDT", res.get("buy_price"), res.get("sell_price"), res.get("gross_profit"), res.get("net_profit"))
            if not res.get("simulated"):
                bal = database.get_user_balance(uid)
                database.set_user_balance(uid, max(0, bal - amount))
            await update.message.reply_text(f"✅ تمت العملية. صافي الربح: {res.get('net_profit'):.2f} USD ({'محاكاة' if res.get('simulated') else 'حقيقية'})")
            clear_state(uid)
            return

    # fallback
    await update.message.reply_text("استخدم /start للعودة للقائمة.")

# register helper
def register_handlers(app):
    from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_router))
# handlers.py
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import database
import utils
from datetime import datetime, timedelta

# state tracking simple dict
user_states = {}  # telegram_id -> dict {state: str, meta: {}}

# keyboards
main_kb = InlineKeyboardMarkup([
    [InlineKeyboardButton("1️⃣ تسجيل أو تعديل بيانات التداول", callback_data="menu_manage_trading")],
    [InlineKeyboardButton("2️⃣ ابدأ استثمار", callback_data="menu_start_invest")],
    [InlineKeyboardButton("3️⃣ استثمار وهمي", callback_data="menu_virtual_invest")],
    [InlineKeyboardButton("4️⃣ كشف حساب عن فترة", callback_data="menu_account_statement")],
    [InlineKeyboardButton("5️⃣ حالة السوق", callback_data="menu_market_status")],
    [InlineKeyboardButton("6️⃣ إيقاف الاستثمار", callback_data="menu_stop_invest")],
])

# manage trading keyboard
manage_kb = InlineKeyboardMarkup([
    [InlineKeyboardButton("➕ إضافة منصة", callback_data="trade_add_platform")],
    [InlineKeyboardButton("✏️ تعديل/عرض المنصات", callback_data="trade_list_platforms")],
    [InlineKeyboardButton("🏦 محفظة المستخدم (الرصيد)", callback_data="trade_wallet")],
    [InlineKeyboardButton("🔙 الرجوع", callback_data="menu_main")],
])

# helper to set state
def set_state(uid, state, meta=None):
    user_states[uid] = {"state": state, "meta": meta or {}}
def clear_state(uid):
    if uid in user_states:
        del user_states[uid]

# start handler (send main menu)
async def start_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    database.ensure_user(uid)
    database.update_last_active(uid)
    await update.message.reply_text("مرحبًا! اختر من القائمة:", reply_markup=main_kb)

# callback router
async def callback_router(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data
    database.update_last_active(uid)

    # main menu navigation
    if data == "menu_main":
        await query.edit_message_text("القائمة الرئيسية:", reply_markup=main_kb)
        clear_state(uid)
        return

    if data == "menu_manage_trading":
        await query.edit_message_text("تسجيل أو تعديل بيانات التداول — اختر:", reply_markup=manage_kb)
        clear_state(uid)
        return

    if data == "trade_add_platform":
        # ask which platform
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("Binance", callback_data="addplat:Binance")],
            [InlineKeyboardButton("KuCoin", callback_data="addplat:KuCoin")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="menu_manage_trading")]
        ])
        await query.edit_message_text("اختر المنصة التي تريد إضافتها:", reply_markup=buttons)
        return

    if data.startswith("addplat:"):
        platform = data.split(":",1)[1]
        set_state(uid, "entering_api_key", {"platform": platform, "step": "api_key"})
        await query.edit_message_text(f"أرسل الآن **{platform} API Key** (أرسل فقط النص):")
        return

    if data == "trade_list_platforms":
        plats = database.get_platforms(uid)
        if not plats:
            await query.edit_message_text("لا توجد منصات مضافة بعد. استخدم 'إضافة منصة'.")
            return
        text_lines = []
        kb = []
        for p in plats:
            status = "✅ مفعل" if p.get("enabled") else "🔴 موقوف"
            text_lines.append(f"{p['platform_name']}: {status}")
            kb.append([InlineKeyboardButton(f"تعديل {p['platform_name']}", callback_data=f"editplat:{p['platform_name']}"),
                       InlineKeyboardButton("إيقاف/تفعيل", callback_data=f"toggleplat:{p['platform_name']}")])
        kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_manage_trading")])
        await query.edit_message_text("\n".join(text_lines), reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("editplat:"):
        platform = data.split(":",1)[1]
        set_state(uid, "entering_api_key", {"platform": platform, "step": "api_key", "editing": True})
        await query.edit_message_text(f"أرسل API Key جديد لـ {platform} (أو أعد إرساله إذا تود تغييره):")
        return

    if data.startswith("toggleplat:"):
        platform = data.split(":",1)[1]
        plats = database.get_platforms(uid)
        target = None
        for p in plats:
            if p["platform_name"].lower() == platform.lower():
                target = p
                break
        if not target:
            await query.edit_message_text("المنصة غير موجودة.")
            return
        new_state = not bool(target.get("enabled"))
        database.set_platform_enabled(uid, platform, new_state)
        await query.edit_message_text(f"تم {'تفعيل' if new_state else 'إيقاف'} منصة {platform}.")
        return

    if data == "trade_wallet":
        bal = database.get_user_balance(uid)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 تعيين/تحديث الرصيد", callback_data="wallet_set")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="menu_manage_trading")]
        ])
        await query.edit_message_text(f"رصيدك الحالي: {bal:.2f} USD", reply_markup=kb)
        return

    if data == "wallet_set":
        set_state(uid, "enter_wallet")
        await query.edit_message_text("أرسل الآن رصيد محفظتك (رقم بالدولار):")
        return

    # account statement: ask start date (last 7 days)
    if data == "menu_account_statement":
        # show last 7 days
        today = datetime.utcnow().date()
        kb_rows = []
        for i in range(7):
            d = today - timedelta(days=i)
            s = d.strftime("%Y-%m-%d")
            kb_rows.append([InlineKeyboardButton(s, callback_data=f"stmt:{s}")])
        kb_rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_main")])
        await query.edit_message_text("اختر بداية الفترة:", reply_markup=InlineKeyboardMarkup(kb_rows))
        return

    if data.startswith("stmt:"):
        start_date = data.split(":",1)[1]
        total = database.get_investments_sum_since(uid, start_date)
        await query.edit_message_text(f"إجمالي الأرباح منذ {start_date}: {total:.2f} USD")
        return

    # start invest (real)
    if data == "menu_start_invest":
        # ask amount or use wallet
        set_state(uid, "start_invest_choose")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 استخدام رصيد المحفظة", callback_data="invest_use_wallet")],
            [InlineKeyboardButton("✏️ إدخال مبلغ جديد", callback_data="invest_enter_amount")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="menu_main")],
        ])
        await query.edit_message_text("اختر طريقة تحديد المبلغ:", reply_markup=kb)
        return

    if data == "invest_use_wallet":
        bal = database.get_user_balance(uid)
        if bal <= 0:
            await query.edit_message_text("رصيدك لا يكفي للاستثمار. يرجى إيداع رصيد أولاً.")
            return
        # confirm use
        set_state(uid, "confirm_invest", {"amount": bal, "type": "real"})
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("نعم ابدأ الآن", callback_data="confirm_invest_yes")],
            [InlineKeyboardButton("لا، إلغاء", callback_data="menu_main")],
        ])
        await query.edit_message_text(f"هل تريد استخدام كامل رصيدك {bal:.2f} USD لبدء الاستثمار؟", reply_markup=kb)
        return

    if data == "invest_enter_amount":
        set_state(uid, "enter_invest_amount", {"type": "real"})
        await query.edit_message_text("أرسل مبلغ الاستثمار (USD):")
        return

    if data == "confirm_invest_yes":
        st = user_states.get(uid)
        if not st or st.get("state") != "confirm_invest":
            await query.edit_message_text("لا توجد عملية للاستمرار فيها.")
            return
        amount = float(st["meta"]["amount"])
        # check platforms
        plats = database.get_platforms(uid)
        if not plats:
            await query.edit_message_text("⚠️ لا توجد منصات مضافة — من فضلك أضف منصة أولاً.")
            return
        # start investing (simple strategy: use first enabled platform)
        platform_entry = None
        for p in plats:
            if p.get("enabled"):
                platform_entry = p
                break
        if not platform_entry:
            await query.edit_message_text("لا توجد منصات مفعلة.")
            return
        await query.edit_message_text("جاري التحقق من مفاتيح المنصة وتنفيذ الصفقة (قد تكون محاكاة حسب إعدادات السيرفر)...")
        res = await utils.execute_real_trade(platform_entry, amount, symbol="BTC/USDT")
        if not res.get("ok"):
            await query.edit_message_text(f"فشل تنفيذ الاستثمار: {res.get('msg')}")
            clear_state(uid)
            return
        # log
        gross = res.get("gross_profit", 0.0)
        net = res.get("net_profit", 0.0)
        database.log_investment(uid, platform_entry["platform_name"], "real", amount, "BTC/USDT", "BTC/USDT", res.get("buy_price"), res.get("sell_price"), gross, net)
        # deduct from balance if real executed? Only when simulated=false
        if not res.get("simulated"):
            bal = database.get_user_balance(uid)
            database.set_user_balance(uid, max(0, bal - amount))
        await query.edit_message_text(
            f"✅ تمت العملية.\nالربح الصافي: {net:.2f} USD\n(المذكور أعلاه {'محاكى' if res.get('simulated') else 'حقيقي'})"
        )
        clear_state(uid)
        return

    # virtual invest entry
    if data == "menu_virtual_invest":
        set_state(uid, "enter_invest_amount", {"type": "virtual"})
        await query.edit_message_text("الاستثمار الوهمي — الرجاء إدخال مبلغ الاستثمار (USD):")
        return

    # market status
    if data == "menu_market_status":
        await query.edit_message_text("جاري تجميع تحليل السوق...")
        # call utils.fetch_ticker and OpenAI via utils.to_thread
        try:
            # fetch some prices
            coins = ["BTC/USDT","ETH/USDT","BNB/USDT"]
            binance = __import__('ccxt').binance()
            tickers = await utils.to_thread(binance.fetch_tickers)
            prices_text = ""
            for c in coins:
                if c in tickers:
                    prices_text += f"{c}: {tickers[c]['last']:.2f} USD\n"
        except Exception:
            prices_text = "تعذر جلب الأسعار حالياً."
        # call OpenAI
        prompt = f"قدم تحليل للسوق ونصائح استثمارية. الأسعار الحالية:\n{prices_text}"
        try:
            # safe call in thread
            resp = await utils.to_thread(__import__('openai').ChatCompletion.create,
                                        model="gpt-4o-mini",
                                        messages=[{"role":"system","content":"أنت مساعد خبير في تداول العملات الرقمية."},
                                                  {"role":"user","content":prompt}],
                                        max_tokens=400, temperature=0.7)
            # parse
            if isinstance(resp, dict):
                analysis = resp.get("choices",[{}])[0].get("message",{}).get("content","")
            else:
                analysis = resp.choices[0].message.content
        except Exception as e:
            analysis = f"تعذر توليد تحليل كامل: {e}"
        full = analysis + "\n\n" + prices_text
        # split large message into parts
        parts = [full[i:i+3800] for i in range(0,len(full),3800)]
        for p in parts:
            await query.message.reply_text(p)
        return

    if data == "menu_stop_invest":
        database.set_user_investing(uid, False)
        await query.edit_message_text("تم إيقاف الاستثمار لحسابك. لن يتم استخدام أموالك مرة أخرى حتى تفعّل بنفسك.")
        return

    # fallback
    await query.edit_message_text("أمر غير معروف - ارجع للقائمة الرئيسية.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة للقائمة", callback_data="menu_main")]]))
