import asyncio
import aiomysql
import os

DATABASE_URL = os.getenv("DATABASE_URL")

REQUIRED_COLUMNS = {
    "id": "INT AUTO_INCREMENT PRIMARY KEY",
    "telegram_id": "BIGINT UNIQUE NOT NULL",
    "binance_api_key": "TEXT",
    "binance_secret_key": "TEXT",
    "kucoin_api_key": "TEXT",
    "kucoin_secret_key": "TEXT",
    "kucoin_passphrase": "TEXT",
    "investment_amount": "DOUBLE DEFAULT 0",
    "mode": "VARCHAR(20) DEFAULT 'live'",
    "wallet_address": "TEXT",
    "total_profit_loss": "DOUBLE DEFAULT 0"
}

async def recreate_table():
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
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # حذف الجدول إذا كان موجودًا
            await cur.execute("DROP TABLE IF EXISTS users;")
            print("Deleted existing table 'users' if existed.")

            # بناء جملة إنشاء الجدول كاملة حسب الأعمدة المطلوبة
            columns_definitions = ",\n".join(f"{col} {typ}" for col, typ in REQUIRED_COLUMNS.items())
            create_table_sql = f"CREATE TABLE users (\n{columns_definitions}\n);"
            await cur.execute(create_table_sql)
            print("Created new table 'users' with defined structure.")

    pool.close()
    await pool.wait_closed()
    print("Database reset completed.")

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    asyncio.run(recreate_table())
