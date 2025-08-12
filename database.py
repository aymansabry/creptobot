# database.py
import os
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv
from urllib.parse import urlparse

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
            invested_amount FLOAT DEFAULT 0,
            profit FLOAT DEFAULT 0,
            is_investing BOOLEAN DEFAULT FALSE
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


def get_user_active_platforms(user_id):
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

def set_user_binance_api(user_id, api_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (telegram_id, binance_api_key) VALUES (%s, %s) "
        "ON DUPLICATE KEY UPDATE binance_api_key=%s",
        (user_id, api_key, api_key),
    )
    conn.commit()
    cursor.close()
    conn.close()

def set_user_binance_secret(user_id, secret_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET binance_secret_key=%s WHERE telegram_id=%s", (secret_key, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def set_user_kucoin_api(user_id, api_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET kucoin_api_key=%s WHERE telegram_id=%s", (api_key, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def set_user_kucoin_secret(user_id, secret_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET kucoin_secret_key=%s WHERE telegram_id=%s", (secret_key, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def set_user_invest_amount(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET invested_amount=%s WHERE telegram_id=%s", (amount, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_user_invest_amount(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT invested_amount FROM users WHERE telegram_id=%s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else 0

def update_user_profit(user_id, profit):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET profit=profit+%s WHERE telegram_id=%s", (profit, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def log_investment_history(user_id, platform, operation, amount, price):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO investment_history (telegram_id, platform, operation, amount, price) VALUES (%s, %s, %s, %s, %s)",
        (user_id, platform, operation, amount, price),
    )
    conn.commit()
    cursor.close()
    conn.close()
