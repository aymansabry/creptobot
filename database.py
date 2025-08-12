import os
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def parse_database_url(url):
    result = urlparse(url)
    return {
        'host': result.hostname,
        'user': result.username,
        'password': result.password,
        'database': result.path.lstrip('/'),
        'port': result.port or 3306,
        'auth_plugin': 'mysql_native_password'
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
                kucoin_password VARCHAR(255),
                invested_amount FLOAT DEFAULT 0,
                profit FLOAT DEFAULT 0,
                wallet_address VARCHAR(255),
                active_platforms JSON DEFAULT '[]',
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INT PRIMARY KEY,
                owner_wallet VARCHAR(255),
                profit_percent FLOAT DEFAULT 5.0
            )
        """)
        # تأكد من وجود سجل اعدادات وحيد
        cursor.execute("SELECT COUNT(*) FROM settings WHERE id=1")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO settings (id, owner_wallet, profit_percent) VALUES (1, %s, %s)",
                           (os.getenv('OWNER_WALLET'), float(os.getenv('PROFIT_PERCENT') or 5.0)))
        conn.commit()
        cursor.close()
        conn.close()

def get_user(telegram_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE telegram_id=%s", (telegram_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def save_user_data(telegram_id, **kwargs):
    conn = get_connection()
    cursor = conn.cursor()
    # تحقق هل المستخدم موجود
    cursor.execute("SELECT id FROM users WHERE telegram_id=%s", (telegram_id,))
    if cursor.fetchone():
        # تحديث الحقول فقط
        for key, value in kwargs.items():
            cursor.execute(f"UPDATE users SET {key}=%s WHERE telegram_id=%s", (value, telegram_id))
    else:
        # إدخال سجل جديد مع الحقول المتاحة
        keys = ', '.join(kwargs.keys())
        vals = tuple(kwargs.values())
        placeholders = ', '.join(['%s'] * len(vals))
        cursor.execute(f"INSERT INTO users (telegram_id, {keys}) VALUES (%s, {placeholders})", (telegram_id, *vals))
    conn.commit()
    cursor.close()
    conn.close()

def get_settings():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM settings WHERE id=1")
    settings = cursor.fetchone()
    cursor.close()
    conn.close()
    return settings

def update_settings(**kwargs):
    conn = get_connection()
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f"UPDATE settings SET {key}=%s WHERE id=1", (value,))
    conn.commit()
    cursor.close()
    conn.close()