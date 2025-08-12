# database.py
import mysql.connector
from mysql.connector import Error
import os

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "railway")

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# --- إنشاء الجداول ---
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            k VARCHAR(255) PRIMARY KEY,
            v VARCHAR(255) NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            role VARCHAR(20) DEFAULT 'client',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS exchanges (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            exchange_name VARCHAR(50) NOT NULL,
            api_key TEXT NOT NULL,
            api_secret TEXT NOT NULL,
            sandbox TINYINT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

# --- إعدادات البوت ---
def set_setting(key, value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO settings (k, v) VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE v=VALUES(v)
    """, (key, value))
    conn.commit()
    cur.close()
    conn.close()

def get_setting(key, default=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT v FROM settings WHERE k=%s", (key,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else default

# --- إدارة المستخدمين ---
def add_user(telegram_id, role="client"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT IGNORE INTO users (telegram_id, role) VALUES (%s, %s)
    """, (telegram_id, role))
    conn.commit()
    cur.close()
    conn.close()

def get_user_id(telegram_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE telegram_id=%s", (telegram_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

# --- إدارة المنصات ---
def save_exchange(user_id, exchange_name, api_key, api_secret, sandbox=False):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO exchanges (user_id, exchange_name, api_key, api_secret, sandbox)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        api_key=VALUES(api_key),
        api_secret=VALUES(api_secret),
        sandbox=VALUES(sandbox)
    """, (user_id, exchange_name, api_key, api_secret, int(sandbox)))
    conn.commit()
    cur.close()
    conn.close()

def get_exchange(user_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM exchanges WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

# --- إيقاف الاستثمار ---
def stop_user_investment(telegram_id):
    # في الحالة الحقيقية، يمكنك تحديث حالة المستخدم أو حذف صفقة حالية
    print(f"📌 تم إيقاف الاستثمار للمستخدم {telegram_id}")

# --- تهيئة قاعدة البيانات عند التشغيل ---
init_db()
