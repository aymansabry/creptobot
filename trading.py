import asyncio
import math
import logging
from typing import List, Dict, Any
from binance import AsyncClient
from binance.enums import ORDER_TYPE_MARKET, SIDE_BUY, SIDE_SELL
from db import get_user_api_keys, add_trade, get_amount

# من المهم جداً استيراد get_amount من ملف db.py

logger = logging.getLogger("trading")
logger.setLevel(logging.INFO)

# متغيرات لحالة التداول
TRADING_RUNNING = {}  # مؤشر لكل مستخدم يحدد ما إذا كانت حلقة التداول قيد التشغيل
USER_CLIENTS = {}      # ذاكرة مؤقتة لعملاء Binance لكل مستخدم
EXCHANGE_INFO_CACHE = {} # ذاكرة مؤقتة لمعلومات ExchangeInfo لتجنب الطلبات المتكررة

async def get_client_for_user(telegram_id: int) -> AsyncClient:
    """
    إنشاء أو إرجاع AsyncClient مخزن مؤقتًا للمستخدم.
    يرفع خطأ ValueError إذا كانت المفاتيح مفقودة.
    """
    if telegram_id in USER_CLIENTS:
        return USER_CLIENTS[telegram_id]

    api_key, api_secret = get_user_api_keys(telegram_id)
    if not api_key or not api_secret:
        raise ValueError("API keys not found for user.")
    
    client = await AsyncClient.create(api_key, api_secret)
    USER_CLIENTS[telegram_id] = client
    return client

async def close_clients():
    """إغلاق جميع اتصالات العملاء المخزنة مؤقتًا."""
    for c in list(USER_CLIENTS.values()):
        try:
            await c.close_connection()
        except Exception:
            pass
    USER_CLIENTS.clear()

async def get_exchange_info(client: AsyncClient, symbol: str) -> Dict[str, Any]:
    """
    جلب معلومات التداول للرمز المحدد مع التخزين المؤقت.
    هذه المعلومات ضرورية لحساب الكميات الدقيقة.
    """
    if symbol in EXCHANGE_INFO_CACHE:
        return EXCHANGE_INFO_CACHE[symbol]

    info = await client.get_symbol_info(symbol=symbol)
    if info:
        EXCHANGE_INFO_CACHE[symbol] = info
    return info

def get_symbol_step_size(info: Dict[str, Any]) -> float:
    """استخراج حجم الخطوة (stepSize) من معلومات الرمز."""
    for f in info['filters']:
        if f['filterType'] == 'LOT_SIZE':
            return float(f['stepSize'])
    return 0.0

def get_symbol_min_notional(info: Dict[str, Any]) -> float:
    """استخراج الحد الأدنى للقيمة (minNotional) من معلومات الرمز."""
    for f in info['filters']:
        if f['filterType'] == 'MIN_NOTIONAL':
            return float(f['minNotional'])
    return 0.0

def floor_quantity_to_step_size(quantity: float, step_size: float) -> float:
    """تقريب الكمية للأسفل لتناسب حجم الخطوة."""
    return math.floor(quantity / step_size) * step_size

async def check_user_balance(client: AsyncClient, trading_amount: float) -> bool:
    """
    التحقق مما إذا كان لدى المستخدم رصيد USDT كافٍ لمبلغ التداول المحدد.
    """
    try:
        info = await client.get_account()
        usdt_balance = 0.0
        for asset in info['balances']:
            if asset['asset'] == 'USDT':
                usdt_balance = float(asset['free'])
                break
        
        if usdt_balance >= trading_amount:
            logger.info(f"Sufficient balance found: {usdt_balance} USDT.")
            return True
        else:
            logger.warning(f"Insufficient balance. Required: {trading_amount} USDT, Available: {usdt_balance} USDT.")
            return False
    except Exception as e:
        logger.error(f"Error checking balance: {e}")
        return False

async def start_arbitrage(telegram_id: int):
    """
    تبدأ حلقة المراجحة طويلة الأمد لكل مستخدم.
    """
    TRADING_RUNNING[telegram_id] = True
    try:
        client = await get_client_for_user(telegram_id)
        trading_amount_usdt = get_amount(telegram_id)
        
        # خطوة حاسمة: التحقق من الرصيد قبل بدء أي شيء
        if not await check_user_balance(client, trading_amount_usdt):
            logger.error(f"Cannot start arbitrage for {telegram_id}: Insufficient balance.")
            TRADING_RUNNING.pop(telegram_id, None)
            return
            
    except Exception as e:
        logger.error(f"cannot start arbitrage for {telegram_id}: {e}")
        TRADING_RUNNING.pop(telegram_id, None)
        return

    logger.info(f"Start arbitrage loop for {telegram_id} with {trading_amount_usdt} USDT.")

    while TRADING_RUNNING.get(telegram_id):
        try:
            opportunities = await calculate_arbitrage_opportunities(client)
            # تنفيذ الفرص بالترتيب (تجربة الفرصة الأولى فقط لتبسيط المثال)
            for opp in opportunities:
                # تمرير مبلغ التداول المحدد من المستخدم
                ok = await execute_arbitrage(client, telegram_id, opp, trading_amount_usdt)
                if ok:
                    logger.info("Executed arbitrage successfully")
                else:
                    logger.info("Arbitrage attempt failed")
                # إذا نجحت أول فرصة، نخرج ونبحث عن فرص جديدة في الحلقة التالية
                break 
            
            await asyncio.sleep(3)  # توقف قصير
        except Exception as e:
            logger.exception("Error in arbitrage loop: %s", e)
            await asyncio.sleep(2)

    logger.info(f"Arbitrage loop stopped for {telegram_id}")

async def stop_arbitrage(telegram_id: int = None):
    """
    إيقاف التداول لمستخدم معين أو لجميع المستخدمين إذا كان telegram_id هو None.
    """
    if telegram_id is None:
        for k in list(TRADING_RUNNING.keys()):
            TRADING_RUNNING[k] = False
        await close_clients()
        logger.info("Stopped all arbitrage loops")
    else:
        TRADING_RUNNING[telegram_id] = False
        # إغلاق اتصال العميل الخاص بهذا المستخدم
        client = USER_CLIENTS.pop(telegram_id, None)
        if client:
            try:
                await client.close_connection()
            except Exception:
                pass
        logger.info(f"Stopped arbitrage for {telegram_id}")

# ----------------- وظائف مساعدة لوضع الأوامر -----------------
async def place_market_order(client: AsyncClient, symbol: str, side: str, quantity: float):
    """
    وضع أمر سوق مع التأكد من مطابقة الكمية لقواعد المنصة.
    """
    try:
        order = await client.create_order(
            symbol=symbol,
            side=side,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )
        logger.info(f"Order placed: {order}")
        return order
    except Exception as e:
        logger.error(f"place_market_order error {symbol} {side} {quantity}: {e}")
        return None

async def get_price(client: AsyncClient, symbol: str) -> float:
    """جلب السعر الحالي للرمز."""
    try:
        ticker = await client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except Exception:
        return 0.0

# ----------------- اكتشاف المراجحة -----------------
async def calculate_arbitrage_opportunities(client: AsyncClient) -> List[Dict[str, Any]]:
    """
    اكتشاف فرص المراجحة الثلاثية، الرباعية، والخماسية.
    تُرجع قائمة بالفرص مرتبة حسب الربح التقديري.
    """
    tickers = await client.get_all_tickers()
    symbols = [t["symbol"] for t in tickers]
    price_map = {t["symbol"]: float(t["price"]) for t in tickers}

    opportunities = []
    # رسوم مبسطة للتداول
    TRADING_FEE = 0.001 # 0.1% for each trade

    def has(sym):
        return sym in price_map

    # --- المراجحة الثلاثية: A/USDT -> A/B -> B/USDT ---
    for s_a_usdt in [s for s in symbols if s.endswith("USDT")]:
        coin_a = s_a_usdt[:-4]
        for s_a_b in [s for s in symbols if s.startswith(coin_a) and s != s_a_usdt]:
            coin_b = s_a_b[len(coin_a):]
            final = f"{coin_b}USDT"
            if not has(final):
                continue
            
            # حساب الربح التقديري
            pa = price_map[s_a_usdt]
            pab = price_map[s_a_b]
            pfinal = price_map[final]
            try:
                # حساب الربح بعد خصم الرسوم
                final_usdt = (1.0 * (1 - TRADING_FEE) / pa) * pab * (1 - TRADING_FEE) * pfinal * (1 - TRADING_FEE)
                est_profit = final_usdt - 1.0
                if est_profit > 0.0001:  # تم خفض عتبة الربح لقبول أرباح ضئيلة جداً (0.01%)
                    opp = {
                        "type": "tri",
                        "path": [s_a_usdt, s_a_b, final],
                        "est_profit_ratio": est_profit,
                    }
                    opportunities.append(opp)
            except Exception:
                continue

    # --- المراجحة الرباعية: A/USDT -> A/B -> B/C -> C/USDT ---
    for s_a_usdt in [s for s in symbols if s.endswith("USDT")]:
        coin_a = s_a_usdt[:-4]
        for s_a_b in [s for s in symbols if s.startswith(coin_a) and s != s_a_usdt]:
            coin_b = s_a_b[len(coin_a):]
            for s_b_c in [s for s in symbols if s.startswith(coin_b) and s not in (s_a_b, s_a_usdt)]:
                coin_c = s_b_c[len(coin_b):]
                final = f"{coin_c}USDT"
                if not has(final):
                    continue
                try:
                    pa = price_map[s_a_usdt]
                    pab = price_map[s_a_b]
                    pbc = price_map[s_b_c]
                    pfinal = price_map[final]
                    final_usdt = (1.0 * (1 - TRADING_FEE) / pa) * pab * (1 - TRADING_FEE) * pbc * (1 - TRADING_FEE) * pfinal * (1 - TRADING_FEE)
                    est_profit = final_usdt - 1.0
                    if est_profit > 0.00015:  # تم خفض العتبة هنا أيضاً (0.015%)
                        opp = {
                            "type": "quad",
                            "path": [s_a_usdt, s_a_b, s_b_c, final],
                            "est_profit_ratio": est_profit,
                        }
                        opportunities.append(opp)
                except Exception:
                    continue

    # --- المراجحة الخماسية (5 خطوات) ---
    for s_a_usdt in [s for s in symbols if s.endswith("USDT")]:
        coin_a = s_a_usdt[:-4]
        for s_a_b in [s for s in symbols if s.startswith(coin_a) and s != s_a_usdt]:
            coin_b = s_a_b[len(coin_a):]
            for s_b_c in [s for s in symbols if s.startswith(coin_b) and s not in (s_a_b, s_a_usdt)]:
                coin_c = s_b_c[len(coin_b):]
                for s_c_d in [s for s in symbols if s.startswith(coin_c) and s not in (s_b_c, s_a_b, s_a_usdt)]:
                    coin_d = s_c_d[len(coin_c):]
                    final = f"{coin_d}USDT"
                    if not has(final):
                        continue
                    try:
                        pa = price_map[s_a_usdt]
                        pab = price_map[s_a_b]
                        pbc = price_map[s_b_c]
                        pcd = price_map[s_c_d]
                        pfinal = price_map[final]
                        final_usdt = (1.0 * (1 - TRADING_FEE) / pa) * pab * (1 - TRADING_FEE) * pbc * (1 - TRADING_FEE) * pcd * (1 - TRADING_FEE) * pfinal * (1 - TRADING_FEE)
                        est_profit = final_usdt - 1.0
                        if est_profit > 0.0002: # تم خفض العتبة أيضاً (0.02%)
                            opp = {
                                "type": "penta",
                                "path": [s_a_usdt, s_a_b, s_b_c, s_c_d, final],
                                "est_profit_ratio": est_profit,
                            }
                            opportunities.append(opp)
                    except Exception:
                        continue

    # فرز الفرص حسب الربح التقديري وإرجاع أفضل 10 فرص
    opportunities.sort(key=lambda x: x["est_profit_ratio"], reverse=True)
    return opportunities[:10]

# ----------------- وظيفة التراجع (Rollback) -----------------
async def sell_to_usdt(client: AsyncClient, asset: str) -> bool:
    """
    وظيفة التراجع: تبيع العملة المحددة إلى USDT في حالة الفشل.
    """
    symbol = f"{asset}USDT"
    try:
        # الحصول على الكمية المتاحة من هذه العملة
        balances = await client.get_account()
        qty = 0.0
        for bal in balances['balances']:
            if bal['asset'] == asset:
                qty = float(bal['free'])
                break

        if qty > 0:
            # الحصول على معلومات الرمز للتأكد من الكمية
            info = await get_exchange_info(client, symbol)
            if not info: return False

            step_size = get_symbol_step_size(info)
            min_notional = get_symbol_min_notional(info)
            
            # تصحيح الكمية لتناسب قواعد المنصة
            corrected_qty = floor_quantity_to_step_size(qty, step_size)
            
            # التحقق من أن الكمية المصححة كافية للبيع
            price = await get_price(client, symbol)
            if corrected_qty * price < min_notional:
                logger.warning(f"Rollback: Corrected quantity {corrected_qty} for {symbol} is too low to sell.")
                return False

            # تنفيذ أمر البيع
            res = await place_market_order(client, symbol, SIDE_SELL, corrected_qty)
            if res:
                logger.info(f"Rollback successful: Sold {corrected_qty} of {asset} to USDT.")
                return True
        return False
    except Exception as e:
        logger.error(f"Rollback failed for {asset}: {e}")
        return False

# ----------------- تنفيذ الفرصة -----------------
async def execute_arbitrage(client: AsyncClient, telegram_id: int, opportunity: dict, usd_amount: float):
    """
    يحول مسار الفرصة إلى أوامر سوق فعلية باستخدام المبلغ المحدد.
    """
    path = opportunity.get("path", [])
    current_asset_quantity = usd_amount  # نبدأ بمبلغ المستخدم
    
    try:
        for i, symbol in enumerate(path):
            info = await get_exchange_info(client, symbol)
            if not info:
                logger.error(f"Could not get exchange info for {symbol}")
                return False

            min_notional = get_symbol_min_notional(info)

            if symbol.endswith("USDT"): # الخطوة الأولى: شراء العملة الأساسية بالـ USDT
                price = await get_price(client, symbol)
                if price <= 0: return False
                
                # حساب الكمية وتصحيحها لتناسب قواعد بينانس
                raw_qty = current_asset_quantity / price
                step_size = get_symbol_step_size(info)
                qty = floor_quantity_to_step_size(raw_qty, step_size)
                
                # التحقق من الحد الأدنى للقيمة
                if qty * price < min_notional:
                    logger.warning(f"Order quantity {qty} for {symbol} is below min notional {min_notional}.")
                    return False
                
                res = await place_market_order(client, symbol, SIDE_BUY, qty)
                if not res: 
                    # إذا فشل الشراء الأول، لا يوجد شيء للبيع، فقط نخرج
                    return False
                
                # تحديث الكمية الحالية بناءً على الكمية التي تم تنفيذها
                current_asset_quantity = float(res['executedQty'])
                
            else: # الخطوات التالية: التبادل بين العملات
                base_asset = info['baseAsset']
                quote_asset = info['quoteAsset']
                
                # تحديد جانب الصفقة (شراء أو بيع)
                if path[i-1].endswith(base_asset):
                    # بيع base_asset للحصول على quote_asset
                    side = SIDE_SELL
                    price = await get_price(client, symbol)
                    if price <= 0: return False

                    raw_qty = current_asset_quantity
                    step_size = get_symbol_step_size(info)
                    qty = floor_quantity_to_step_size(raw_qty, step_size)
                    
                    if qty * price < min_notional:
                        logger.warning(f"Order quantity {qty} for {symbol} is below min notional {min_notional}.")
                        return False
                    
                    res = await place_market_order(client, symbol, side, qty)
                    if not res: 
                        # فشل البيع: نبيع الأصول العالقة إلى USDT
                        await sell_to_usdt(client, base_asset)
                        return False
                    
                    current_asset_quantity = float(res['executedQty'])
                else:
                    # شراء base_asset بـ quote_asset
                    side = SIDE_BUY
                    price = await get_price(client, symbol)
                    if price <= 0: return False
                    
                    # الكمية هنا هي كمية quote_asset التي لدينا
                    raw_qty = current_asset_quantity / price
                    step_size = get_symbol_step_size(info)
                    qty = floor_quantity_to_step_size(raw_qty, step_size)

                    if qty * price < min_notional:
                        logger.warning(f"Order quantity {qty} for {symbol} is below min notional {min_notional}.")
                        return False

                    res = await place_market_order(client, symbol, side, qty)
                    if not res: 
                        # فشل الشراء: نبيع الأصول العالقة إلى USDT
                        await sell_to_usdt(client, quote_asset)
                        return False
                    
                    current_asset_quantity = float(res['executedQty'])

        # إذا وصلت هذه النقطة، فإن جميع الأوامر قد تمت بنجاح
        # تسجيل الصفقة في قاعدة البيانات
        final_usdt_quantity = current_asset_quantity
        profit = final_usdt_quantity - usd_amount
        add_trade(telegram_id, ",".join(path), profit)
        logger.info(f"Arbitrage success! Final profit: {profit} USDT.")
        return True
    
    except Exception as e:
        logger.exception("execute_arbitrage error: %s", e)
        # في حالة وجود أي خطأ غير متوقع، نحاول بيع الأصول المتبقية إلى USDT
        path_assets = [p.replace('USDT', '') for p in path]
        current_asset = path_assets[i]
        await sell_to_usdt(client, current_asset)
        return False
