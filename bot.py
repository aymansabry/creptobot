from sqlalchemy import and_
from cryptography.fernet import InvalidToken

# ... استيراد باقي المكتبات كما هي

# دالة لفك التشفير مع التعامل مع الخطأ
def safe_decrypt(token):
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        return None

# رسالة طلب مبلغ الاستثمار وتحقق الرصيد (مبسط)
@dp.message(Text("ابدأ استثمار"))
async def start_investment(message: types.Message, state: FSMContext):
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("يجب تسجيل بيانات التداول أولاً عبر 'تسجيل/تعديل بيانات التداول'.")
            return
        if not user.is_active:
            await message.answer("تم إيقاف الاستثمار الخاص بك، لا يمكنك البدء حالياً.")
            return
    await message.answer("أدخل مبلغ الاستثمار (مثلاً: 1000):", reply_markup=ReplyKeyboardRemove())
    await state.set_state("waiting_for_investment_amount")

@dp.message(state="waiting_for_investment_amount")
async def process_investment_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("يرجى إدخال مبلغ صحيح أكبر من صفر.")
        return

    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("لم يتم العثور على بيانات المستخدم.")
            await state.clear()
            return

        # هنا يمكن التحقق من رصيد المستخدم الحقيقي من API أو تخزين داخلي
        # مؤقتاً سنفترض رصيد كافٍ
        user.investment_amount = amount
        user.is_active = True
        session.commit()

    await message.answer(f"تم تعيين مبلغ الاستثمار: {amount} بنجاح.\nيتم الآن بدء الاستثمار الآلي...")
    await state.clear()

    # بدء استثمار (بسيط جدًا كمثال)
    await run_investment_for_user(user)

async def run_investment_for_user(user: User):
    # هذه دالة تجريبية لتنفيذ صفقة واحدة لكل منصة مفعلة
    with SessionLocal() as session:
        api_keys = session.query(APIKey).filter(
            APIKey.user_id == user.id,
            APIKey.is_active == True
        ).all()

    for key in api_keys:
        exchange_name = key.exchange
        api_key = safe_decrypt(key.api_key_encrypted)
        api_secret = safe_decrypt(key.api_secret_encrypted)
        passphrase = safe_decrypt(key.passphrase_encrypted) if key.passphrase_encrypted else None
        if not api_key or not api_secret:
            continue  # تخطي المفاتيح غير الصالحة

        try:
            exchange_class = getattr(ccxt, exchange_name)
            params = {}
            if passphrase:
                params['password'] = passphrase
            exchange = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
                **params
            })
            await asyncio.to_thread(exchange.load_markets)

            symbol = 'BTC/USDT'  # كمثال
            amount = 0.001  # كمية صغيرة للعرض

            # تنفيذ أمر شراء (كمثال)
            order = await asyncio.to_thread(exchange.create_market_buy_order, symbol, amount)

            # تسجيل العملية في قاعدة البيانات
            with SessionLocal() as session:
                trade_log = TradeLog(
                    user_id=user.id,
                    exchange=exchange_name,
                    side='buy',
                    symbol=symbol,
                    qty=amount,
                    price=order['average'] if 'average' in order else 0,
                    profit=None,
                    raw=str(order),
                    status='OK',
                    error=None
                )
                session.add(trade_log)
                session.commit()

        except Exception as e:
            # سجل الخطأ
            with SessionLocal() as session:
                trade_log = TradeLog(
                    user_id=user.id,
                    exchange=exchange_name,
                    side='buy',
                    symbol='BTC/USDT',
                    qty=amount,
                    price=0,
                    profit=None,
                    raw='',
                    status='ERROR',
                    error=str(e)
                )
                session.add(trade_log)
                session.commit()

# جلب تقارير استثمارية حقيقية من trade_logs
@dp.message(Text("تقارير الاستثمار"))
async def investment_reports(message: types.Message, state: FSMContext):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return

    await message.answer("أدخل تاريخ بداية التقرير بصيغة YYYY-MM-DD:", reply_markup=ReplyKeyboardRemove())
    await state.set_state("waiting_report_start")

@dp.message(state="waiting_report_start")
async def process_report_start(message: types.Message, state: FSMContext):
    import datetime
    try:
        start_date = datetime.datetime.strptime(message.text.strip(), "%Y-%m-%d")
    except Exception:
        await message.answer("تاريخ غير صالح. الرجاء إدخال تاريخ بصيغة YYYY-MM-DD.")
        return

    await state.update_data(report_start=start_date)
    await message.answer("أدخل تاريخ نهاية التقرير بصيغة YYYY-MM-DD:")
    await state.set_state("waiting_report_end")

@dp.message(state="waiting_report_end")
async def process_report_end(message: types.Message, state: FSMContext):
    import datetime
    try:
        end_date = datetime.datetime.strptime(message.text.strip(), "%Y-%m-%d")
    except Exception:
        await message.answer("تاريخ غير صالح. الرجاء إدخال تاريخ بصيغة YYYY-MM-DD.")
        return

    data = await state.get_data()
    start_date = data.get("report_start")

    with SessionLocal() as session:
        trades = session.query(TradeLog).filter(
            and_(
                TradeLog.created_at >= start_date,
                TradeLog.created_at <= end_date
            )
        ).all()

    if not trades:
        await message.answer(f"لا توجد صفقات بين {start_date.date()} و {end_date.date()}.")
        await state.clear()
        return

    # بناء تقرير مبسط
    report = f"تقارير التداول من {start_date.date()} إلى {end_date.date()}:\n\n"
    for trade in trades[:20]:  # عرض أول 20 صفقة فقط لتجنب طول الرسالة
        report += (
            f"مستخدم: {trade.user_id}, منصة: {trade.exchange}, {trade.side} {trade.qty} {trade.symbol} "
            f"بسعر {trade.price}, حالة: {trade.status}\n"
        )
    if len(trades) > 20:
        report += f"\n... وعدد الصفقات الكلي: {len(trades)}"

    await message.answer(report)
    await state.clear()