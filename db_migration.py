import asyncio
import aiomysql
import os

DATABASE_URL = os.getenv("DATABASE_URL")

# الأعمدة المطلوبة مع أنواعها
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
    # ترجع dict بالاسم والنوع فقط
    return {row[0]: row[1] for row in rows}

def normalize_type(col_type: str) -> str:
    """
    دالة تساعد على تطبيع نوع العمود للمقارنة
    تتجاهل فروقات حالة الحروف ومساحات
    """
    return col_type.lower().replace('unsigned', '').strip()

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
            # أنشئ الجدول إذا لم يكن موجوداً
            await cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL
            );
            """)
            existing_columns = await get_existing_columns(cur, "users")
            print(f"الأعمدة الحالية: {existing_columns}")

            # أضف الأعمدة الناقصة وعدل الأعمدة التي تختلف في النوع
            for col, col_type in REQUIRED_COLUMNS.items():
                if col not in existing_columns:
                    print(f"إضافة العمود الناقص: {col} {col_type}")
                    await cur.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
                else:
                    # قارن نوع العمود الحالي مع المطلوب، وصحح إذا اختلف
                    current_type = normalize_type(existing_columns[col])
                    required_type = normalize_type(col_type)
                    if current_type != required_type:
                        print(f"تعديل نوع العمود: {col} من {existing_columns[col]} إلى {col_type}")
                        await cur.execute(f"ALTER TABLE users MODIFY COLUMN {col} {col_type}")

            # حذف الأعمدة الزائدة غير المطلوبة
            for col in existing_columns:
                if col not in REQUIRED_COLUMNS:
                    print(f"حذف العمود الزائد: {col}")
                    await cur.execute(f"ALTER TABLE users DROP COLUMN {col}")

    pool.close()
    await pool.wait_closed()
    print("تم فحص وتحديث جدول 'users' بنجاح.")

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    asyncio.run(update_table_structure())
