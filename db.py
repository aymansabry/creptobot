import aiomysql
import os

DATABASE_URL = os.getenv("DATABASE_URL")
db_pool = None

async def init_db_pool():
    global db_pool
    if db_pool is None:
        import urllib.parse
        parsed = urllib.parse.urlparse(DATABASE_URL)
        db_pool = await aiomysql.create_pool(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            db=parsed.path.lstrip('/'),
            autocommit=True
        )

async def fetch_live_users():
    await init_db_pool()
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM users WHERE mode='live'")
            users = await cur.fetchall()
            return users

async def get_user_by_telegram_id(telegram_id):
    await init_db_pool()
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM users WHERE telegram_id=%s", (telegram_id,))
            user = await cur.fetchone()
            return user

async def save_user_data(telegram_id, data: dict):
    """
    حفظ أو تحديث بيانات المستخدم في قاعدة البيانات.
    data: dict يحتوي المفاتيح المشفرة ومبلغ الاستثمار والوضع
    """
    await init_db_pool()
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            # تحقق إذا المستخدم موجود
            await cur.execute("SELECT id FROM users WHERE telegram_id=%s", (telegram_id,))
            exists = await cur.fetchone()
            if exists:
                # تحديث البيانات
                await cur.execute("""
                    UPDATE users SET
                        binance_api_key=%s,
                        binance_secret_key=%s,
                        kucoin_api_key=%s,
                        kucoin_secret_key=%s,
                        kucoin_passphrase=%s,
                        investment_amount=%s,
                        mode=%s
                    WHERE telegram_id=%s
                """, (
                    data['binance_api_key'],
                    data['binance_secret_key'],
                    data['kucoin_api_key'],
                    data['kucoin_secret_key'],
                    data['kucoin_passphrase'],
                    data['investment_amount'],
                    data['mode'],
                    telegram_id
                ))
            else:
                # إدخال بيانات جديدة
                await cur.execute("""
                    INSERT INTO users (
                        telegram_id, binance_api_key, binance_secret_key,
                        kucoin_api_key, kucoin_secret_key, kucoin_passphrase,
                        investment_amount, mode
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    telegram_id,
                    data['binance_api_key'],
                    data['binance_secret_key'],
                    data['kucoin_api_key'],
                    data['kucoin_secret_key'],
                    data['kucoin_passphrase'],
                    data['investment_amount'],
                    data['mode']
                ))

async def fetch_all_users():
    await init_db_pool()
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT telegram_id, total_profit_loss FROM users")
            users = await cur.fetchall()
            return users
