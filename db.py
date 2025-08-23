import aiomysql
import asyncio
import os

# DATABASE_URL بالشكل: mysql://user:password@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL")

# تحليل URL
def parse_database_url(url):
    # mysql://user:password@host:port/dbname
    if not url:
        raise ValueError("DATABASE_URL غير معرف")
    prefix, rest = url.split("://")
    userpass, hostportdb = rest.split("@")
    user, password = userpass.split(":")
    hostport, db = hostportdb.split("/")
    host, port = hostport.split(":")
    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "db": db
    }

DB_CONFIG = parse_database_url(DATABASE_URL)

async def get_connection():
    return await aiomysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        db=DB_CONFIG["db"],
    )

# --- دوال المستخدمين ---
async def create_user(user_id, username):
    conn = await get_connection()
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT IGNORE INTO users (user_id, username) VALUES (%s, %s)",
            (user_id, username)
        )
        await conn.commit()
    conn.close()

async def save_api_keys(user_id, api_key, api_secret):
    conn = await get_connection()
    async with conn.cursor() as cur:
        await cur.execute(
            "UPDATE users SET api_key=%s, api_secret=%s WHERE user_id=%s",
            (api_key, api_secret, user_id)
        )
        await conn.commit()
    conn.close()

async def get_user_api_keys(user_id):
    conn = await get_connection()
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT api_key, api_secret FROM users WHERE user_id=%s",
            (user_id,)
        )
        result = await cur.fetchone()
    conn.close()
    return result

async def save_amount(user_id, amount):
    conn = await get_connection()
    async with conn.cursor() as cur:
        await cur.execute(
            "UPDATE users SET amount=%s WHERE user_id=%s",
            (amount, user_id)
        )
        await conn.commit()
    conn.close()

async def get_amount(user_id):
    conn = await get_connection()
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT amount FROM users WHERE user_id=%s",
            (user_id,)
        )
        result = await cur.fetchone()
    conn.close()
    if result:
        return result[0]
    return None
