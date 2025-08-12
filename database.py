import os
import mysql.connector
from mysql.connector import Error
from urllib.parse import urlparse

# قراءة DATABASE_URL من المتغيرات البيئية
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise ValueError("❌ لم يتم تحديد DATABASE_URL في المتغيرات البيئية")

# تحليل رابط الاتصال
url = urlparse(DATABASE_URL)
DB_CONFIG = {
    'host': url.hostname,
    'user': url.username,
    'password': url.password,
    'database': url.path[1:],  # إزالة "/"
    'port': url.port or 3306
}


def get_connection():
    """إنشاء اتصال بقاعدة البيانات."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
        raise


def init_db():
    """إنشاء الجداول إذا لم تكن موجودة."""
    conn = get_connection()
    cursor = conn.cursor()

    # جدول الإعدادات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            k VARCHAR(255) PRIMARY KEY,
            v TEXT
        )
    """)

    # جدول المستخدمين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            role VARCHAR(20) DEFAULT 'client'
        )
    """)

    # جدول مفاتيح API للمنصات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exchange_keys (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            exchange_name VARCHAR(50),
            api_key TEXT,
            api_secret TEXT,
            api_passphrase TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # جدول الصفقات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            exchange_name VARCHAR(50),
            trade_type VARCHAR(10),
            symbol VARCHAR(20),
            amount DECIMAL(18,8),
            price DECIMAL(18,8),
            profit DECIMAL(18,8),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


def get_setting(key, default=None):
    """قراءة إعداد من جدول settings."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT v FROM settings WHERE k=%s", (key,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else default


def set_setting(key, value):
    """حفظ أو تعديل إعداد في جدول settings."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (k, v) VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE v=%s
    """, (key, value, value))
    conn.commit()
    cursor.close()
    conn.close()


# تهيئة قاعدة البيانات عند تشغيل المشروع
init_db()
