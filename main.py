# --- 4. Helper Functions (Async CCXT) ---
import ccxt.async_support as ccxt  # نسخة async من ccxt

# Unified function to create exchange clients
async def create_exchange_client(user_api_keys, platform_name):
    platform_info = user_api_keys.get(platform_name)
    if not platform_info:
        return None

    try:
        # Platforms that require a passphrase (like Kucoin, OKX, Bybit)
        if platform_name in ['kucoin', 'okx', 'bybit'] and 'passphrase' in platform_info:
            exchange = getattr(ccxt, platform_name)({
                'apiKey': platform_info['key'],
                'secret': platform_info['secret'],
                'password': platform_info['passphrase'],
            })
        else:
            exchange = getattr(ccxt, platform_name)({
                'apiKey': platform_info['key'],
                'secret': platform_info['secret'],
            })
        return exchange
    except Exception as e:
        logging.error(f"Error creating client for {platform_name}: {e}")
        return None

# Unified function to verify API keys
async def verify_exchange_keys(platform_name, api_key, secret_key, passphrase=None):
    exchange = None
    try:
        if platform_name in ['kucoin', 'okx', 'bybit'] and passphrase:
            exchange = getattr(ccxt, platform_name)({
                'apiKey': api_key,
                'secret': secret_key,
                'password': passphrase,
            })
        else:
            exchange = getattr(ccxt, platform_name)({
                'apiKey': api_key,
                'secret': secret_key,
            })
        await exchange.load_markets()
        return True
    except Exception as e:
        logging.error(f"Failed to verify {platform_name} keys: {e}")
        return False
    finally:
        if exchange:
            await exchange.close()

# --- 7. Arbitrage Loop Logic (Async Safe) ---
async def run_arbitrage_loop(user_telegram_id, bot: Bot):
    while True:
        with SessionLocal() as db:
            user = db.query(User).filter_by(telegram_id=user_telegram_id).first()
            if not user or user.investment_status != "started":
                return

            if user.max_daily_loss > 0 and user.current_daily_loss >= user.max_daily_loss:
                user.investment_status = "stopped"
                db.commit()
                await bot.send_message(user_telegram_id, "🛑 تم إيقاف الاستثمار تلقائيًا بسبب الوصول إلى الحد الأقصى للخسارة اليومية.")
                return

            if not user.is_api_keys_valid():
                user.investment_status = "stopped"
                db.commit()
                await bot.send_message(user_telegram_id, "❌ تم إيقاف الاستثمار بسبب وجود خطأ في مفاتيح API. يرجى إعادة ضبطها من قائمة الإعدادات.")
                return

            user_keys = user.get_api_keys
            available_platforms = [p for p, k in user_keys.items() if k.get('active')]
            if len(available_platforms) < 2:
                await bot.send_message(user_telegram_id, "❌ يجب تفعيل منصتين على الأقل للاستثمار.")
                user.investment_status = "stopped"
                db.commit()
                continue

            try:
                for trade_pair in json.loads(user.trade_pairs):
                    prices = {}
                    exchanges = {}
                    for platform_name in available_platforms:
                        exchange_client = await create_exchange_client(user_keys, platform_name)
                        if not exchange_client:
                            continue
                        try:
                            ticker = await exchange_client.fetch_ticker(trade_pair)
                            prices[platform_name] = ticker
                            exchanges[platform_name] = exchange_client
                        except Exception as e:
                            logging.error(f"Could not fetch ticker from {platform_name}: {e}")
                            await exchange_client.close()

                    if len(prices) < 2:
                        # Close any open clients
                        for ex in exchanges.values():
                            await ex.close()
                        continue

                    best_buy_platform = min(prices, key=lambda p: prices[p]['ask'])
                    best_sell_platform = max(prices, key=lambda p: prices[p]['bid'])
                    buy_price = prices[best_buy_platform]['ask']
                    sell_price = prices[best_sell_platform]['bid']
                    profit_percentage = ((sell_price - buy_price) / buy_price) * 100

                    if profit_percentage > user.min_profit_percentage:
                        buy_exchange_client = exchanges[best_buy_platform]
                        sell_exchange_client = exchanges[best_sell_platform]

                        balance = await buy_exchange_client.fetch_balance()
                        available_balance = balance['total'].get('USDT', 0)
                        amount_to_trade = min(user.investment_amount, available_balance)

                        if amount_to_trade > 0:
                            try:
                                buy_order = await buy_exchange_client.create_market_buy_order(trade_pair, amount_to_trade / buy_price)
                                await asyncio.sleep(0.5)
                                sell_order = await sell_exchange_client.create_market_sell_order(trade_pair, buy_order['amount'])
                                actual_profit = sell_order['cost'] - buy_order['cost']
                                bot_share = actual_profit * 0.10
                                user_profit = actual_profit - bot_share
                                user.profit_share_owed += bot_share

                                trade_log = TradeLog(
                                    user_id=user.id,
                                    trade_type=f"Buy {best_buy_platform.capitalize()} / Sell {best_sell_platform.capitalize()}",
                                    amount=buy_order['amount'],
                                    profit=user_profit
                                )
                                db.add(trade_log)
                                db.commit()
                                await bot.send_message(user_telegram_id, f"✅ تمت صفقة مراجحة ناجحة على {trade_pair}!\nالربح الصافي: {user_profit:.2f} USDT")
                            except Exception as trade_e:
                                logging.error(f"Error executing trade for user {user.id}: {trade_e}")
                        # Close clients after trade
                        for ex in exchanges.values():
                            await ex.close()

            except Exception as e:
                logging.error(f"Error in arbitrage loop for user {user.id}: {e}")

        await asyncio.sleep(60)
