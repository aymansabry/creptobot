# database.py
import mysql.connector
from mysql.connector import Error
import os

# ==============================
# الاتصال بقاعدة البيانات
# ==============================
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

# ==============================
# إنشاء الجداول
# ==============================
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # جدول الإعدادات
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            k VARCHAR(255) PRIMARY KEY,
            v TEXT
        )
    """)
    # جدول المستخدمين
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            role VARCHAR(20) DEFAULT 'client',
            investment_amount DECIMAL(18,8) DEFAULT 0
        )
    """)
    # جدول مفاتيح API
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            platform VARCHAR(50),
            api_key TEXT,
            api_secret TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

# ==============================
# إعدادات البوت
# ==============================
def get_setting(key, default=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT v FROM settings WHERE k=%s", (key,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO settings (k, v) VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE v = VALUES(v)
    """, (key, value))
    conn.commit()
    cur.close()
    conn.close()

# ==============================
# إدارة المستخدمين
# ==============================
def get_user_by_telegram_id(telegram_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE telegram_id=%s", (telegram_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def add_user(telegram_id, role='client'):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT IGNORE INTO users (telegram_id, role) VALUES (%s, %s)", (telegram_id, role))
    conn.commit()
    cur.close()
    conn.close()

def update_investment_amount(telegram_id, amount):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET investment_amount=%s WHERE telegram_id=%s", (amount, telegram_id))
    conn.commit()
    cur.close()
    conn.close()

# ==============================
# إدارة مفاتيح API
# ==============================
def save_user_api(telegram_id, platform, api_key, api_secret):
    user = get_user_by_telegram_id(telegram_id)
    if not user:
        add_user(telegram_id)
        user = get_user_by_telegram_id(telegram_id)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO api_keys (user_id, platform, api_key, api_secret)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE api_key=VALUES(api_key), api_secret=VALUES(api_secret)
    """, (user['id'], platform, api_key, api_secret))
    conn.commit()
    cur.close()
    conn.close()
