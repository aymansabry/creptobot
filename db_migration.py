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

async def get_existing_columns(cursor, table_name):
    await cursor.execute(f"SHOW COLUMNS FROM {table_name}")
    rows = await cursor.fetchall()
    return {row[0]: row[1] for row in rows}

async def update_table_structure():
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
            await cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL
            );
            """)
            existing_columns = await get_existing_columns(cur, "users")

            for col, col_type in REQUIRED_COLUMNS.items():
                if col not in existing_columns:
                    print(f"Adding missing column: {col}")
                    await cur.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
    pool.close()
    await pool.wait_closed()
    print("Table 'users' checked and updated successfully.")

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    asyncio.run(update_table_structure())
