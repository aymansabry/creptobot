import aiomysql
import os

DATABASE_URL = os.getenv("DATABASE_URL")

async def get_pool():
    import urllib.parse
    parsed = urllib.parse.urlparse(DATABASE_URL)
    pool = await aiomysql.create_pool(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=parsed.username,
        password=parsed.password,
        db=parsed.path.lstrip('/'),
        autocommit=True
    )
    return pool

async def save_user_data(telegram_id: int, data: dict):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # تحقق هل المستخدم موجود
            await cur.execute("SELECT id FROM users WHERE telegram_id=%s", (telegram_id,))
            res = await cur.fetchone()
            if res:
                # حدث البيانات
                await cur.execute("""
                    UPDATE users SET
                        binance_api_key=%s,
                        binance_secret_key=%s,
                        kucoin_api_key=%s,
                        kucoin_secret_key=%s,
                        kucoin_passphrase=%s,
                        investment_amount=%s,
                        mode=%s,
                        wallet_address=%s
                    WHERE telegram_id=%s
                """, (
                    data.get("binance_api_key"),
                    data.get("binance_secret_key"),
                    data.get("kucoin_api_key"),
                    data.get("kucoin_secret_key"),
                    data.get("kucoin_passphrase"),
                    data.get("investment_amount"),
                    data.get("mode"),
                    data.get("wallet_address"),
                    telegram_id
                ))
            else:
                # إدخال مستخدم جديد
                await cur.execute("""
                    INSERT INTO users (
                        telegram_id,
                        binance_api_key,
                        binance_secret_key,
                        kucoin_api_key,
                        kucoin_secret_key,
                        kucoin_passphrase,
                        investment_amount,
                        mode,
                        wallet_address,
                        total_profit_loss
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,0)
                """, (
                    telegram_id,
                    data.get("binance_api_key"),
                    data.get("binance_secret_key"),
                    data.get("kucoin_api_key"),
                    data.get("kucoin_secret_key"),
                    data.get("kucoin_passphrase"),
                    data.get("investment_amount"),
                    data.get("mode"),
                    data.get("wallet_address"),
                ))
    pool.close()
    await pool.wait_closed()

async def fetch_all_users():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM users")
            rows = await cur.fetchall()
    pool.close()
    await pool.wait_closed()
    return rows

async def fetch_live_users():
    # مثال: جلب كل المستخدمين بوضع live فقط
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM users WHERE mode='live'")
            rows = await cur.fetchall()
    pool.close()
    await pool.wait_closed()
    return rows

async def update_user_balance(telegram_id: int, profit_loss: float):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET total_profit_loss = total_profit_loss + %s WHERE telegram_id=%s",
                              (profit_loss, telegram_id))
    pool.close()
    await pool.wait_closed()
