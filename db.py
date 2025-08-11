import aiomysql
import os

DATABASE_URL = os.getenv("DATABASE_URL")

db_pool = None

async def init_db_pool():
    global db_pool
    if db_pool is None:
        import urllib.parse
        # مثال لصيغة DATABASE_URL: mysql://user:pass@host:3306/dbname
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

async def update_user_balance(telegram_id, profit_loss):
    await init_db_pool()
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE users SET investment_amount = investment_amount + %s, total_profit_loss = COALESCE(total_profit_loss, 0) + %s WHERE telegram_id = %s",
                (profit_loss, profit_loss, telegram_id)
            )

async def get_user_by_telegram_id(telegram_id):
    await init_db_pool()
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM users WHERE telegram_id=%s", (telegram_id,))
            user = await cur.fetchone()
            return user

async def mark_user_stopped(telegram_id):
    await init_db_pool()
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET mode='stopped' WHERE telegram_id=%s", (telegram_id,))
