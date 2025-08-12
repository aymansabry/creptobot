# database.py
import mysql.connector
from mysql.connector import Error
import os

# قراءة بيانات الاتصال من البيئة
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "bot_db")

def get_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except Error as e:
        print(f"[DB] Connection error: {e}")
        return None

def init_db():
    conn = get_connection()
    if conn:
        cur = conn.cursor()

        # إنشاء جدول المستخدمين
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                telegram_id BIGINT UNIQUE,
                role VARCHAR(20) DEFAULT 'client'
            )
        """)

        # إنشاء جدول المحافظ
        cur.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                exchange_name VARCHAR(50),
                api_key TEXT,
                api_secret TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # إنشاء جدول الإعدادات
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                k VARCHAR(100) UNIQUE,
                v TEXT
            )
        """)

        # إنشاء جدول الصفقات
        cur.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                exchange_name VARCHAR(50),
                symbol VARCHAR(20),
                side VARCHAR(10),
                price DECIMAL(18,8),
                amount DECIMAL(18,8),
                profit_loss DECIMAL(18,8),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # إنشاء جدول السجلات
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("[DB] Database initialized successfully.")

def get_setting(key, default=None):
    conn = get_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT v FROM settings WHERE k=%s", (key,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else default
    return default

def set_setting(key, value):
    conn = get_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO settings (k, v) VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE v=%s
        """, (key, value, value))
        conn.commit()
        cur.close()
        conn.close()

# تنفيذ إنشاء الجداول عند تشغيل الملف
if __name__ == "__main__":
    init_db()
