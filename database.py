import os
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
import asyncio

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def parse_database_url(url):
    result = urlparse(url)
    return {
        "host": result.hostname,
        "user": result.username,
        "password": result.password,
        "database": result.path.lstrip("/"),
        "port": result.port or 3306,
        "auth_plugin": "mysql_native_password",
    }

db_config = parse_database_url(DATABASE_URL)

executor = ThreadPoolExecutor(max_workers=5)

def get_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("خطأ في اسم المستخدم أو كلمة المرور")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("قاعدة البيانات غير موجودة")
        else:
            print(err)
        return None

# تنفيذ استعلامات blocking في threadpool لتجنب حظر الـ event loop
async def run_in_threadpool(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args))

def create_tables():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            binance_api_key VARCHAR(255),
            binance_secret_key VARCHAR(255),
            kucoin_api_key VARCHAR(255),
            kucoin_secret_key VARCHAR(255),
            kucoin_password VARCHAR(255),
            invested_amount FLOAT DEFAULT 0,
            profit FLOAT DEFAULT 0,
            active_platforms JSON NULL,
            is_investing BOOLEAN DEFAULT FALSE
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS owner_wallet (
            id INT PRIMARY KEY CHECK (id = 1),
            wallet_address VARCHAR(255),
            profit_percentage FLOAT DEFAULT 10
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS investment_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT,
            platform VARCHAR(50),
            operation VARCHAR(20),
            amount FLOAT,
            price FLOAT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.close()
        conn.commit()
        conn.close()

# دوال DB متزامنة (تستخدم داخل run_in_threadpool)

def db_get_user_api_keys(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT binance_api_key, binance_secret_key, kucoin_api_key, kucoin_secret_key, kucoin_password FROM users WHERE telegram_id=%s",
        (user_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def db_set_user_binance_api(user_id, api_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (telegram_id, binance_api_key) VALUES (%s, %s) ON DUPLICATE KEY UPDATE binance_api_key=%s",
        (user_id, api_key, api_key),
    )
    conn.commit()
    cursor.close()
    conn.close()

def db_set_user_binance_secret(user_id, secret_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET binance_secret_key=%s WHERE telegram_id=%s", (secret_key, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def db_set_user_kucoin_api(user_id, api_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET kucoin_api_key=%s WHERE telegram_id=%s", (api_key, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def db_set_user_kucoin_secret(user_id, secret_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET kucoin_secret_key=%s WHERE telegram_id=%s", (secret_key, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def db_set_user_kucoin_password(user_id, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET kucoin_password=%s WHERE telegram_id=%s", (password, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def db_set_user_invest_amount(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET invested_amount=%s WHERE telegram_id=%s", (amount, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def db_get_user_profit(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT profit FROM users WHERE telegram_id=%s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else 0

def db_set_user_investing_status(user_id, active: bool):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_investing=%s WHERE telegram_id=%s", (active, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def db_get_active_platforms(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT binance_api_key, kucoin_api_key FROM users WHERE telegram_id=%s", (user_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    platforms = []
    if row:
        if row[0]:
            platforms.append("binance")
        if row[1]:
            platforms.append("kucoin")
    return platforms

def db_insert_investment_history(telegram_id, platform, operation, amount, price):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO investment_history (telegram_id, platform, operation, amount, price) VALUES (%s, %s, %s, %s, %s)",
        (telegram_id, platform, operation, amount, price),
    )
    conn.commit()
    cursor.close()
    conn.close()

def db_get_account_statement(user_id, start_date):
    conn = get_connection()
    cursor = conn.cursor()
    # افترضنا أن جدول trades يحتوي على trade_date و profit
    cursor.execute(
        "SELECT SUM(profit) FROM investment_history WHERE telegram_id=%s AND timestamp >= %s",
        (user_id, start_date),
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    total_profit = result[0] if result and result[0] else 0
    return total_profit
