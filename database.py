# database.py
import mysql.connector
from mysql.connector import Error
import os

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "trading_bot")

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

def init_db():
    """إنشاء الجداول وإضافة الإعدادات الافتراضية إذا لم تكن موجودة"""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn.commit()
        conn.close()

        conn = get_connection()
        cursor = conn.cursor()

        # جدول المستخدمين
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            role VARCHAR(20) DEFAULT 'client',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # جدول حسابات التداول
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_accounts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            platform VARCHAR(50),
            api_key VARCHAR(255),
            api_secret VARCHAR(255),
            active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # جدول المحفظة
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            balance DECIMAL(18,8) DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # جدول الإعدادات العامة
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            k VARCHAR(50) PRIMARY KEY,
            v VARCHAR(255)
        )
        """)

        # جدول الصفقات
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            platform VARCHAR(50),
            symbol VARCHAR(50),
            side VARCHAR(10),
            amount DECIMAL(18,8),
            price DECIMAL(18,8),
            profit DECIMAL(18,8),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # إضافة إعداد افتراضي إذا مش موجود
        cursor.execute("SELECT COUNT(*) FROM settings WHERE k='bot_fee_percent'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO settings (k, v) VALUES (%s, %s)", ("bot_fee_percent", "10"))

        conn.commit()
        conn.close()
        print("✅ قاعدة البيانات جاهزة.")

    except Error as e:
        print(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")

def get_setting(key, default=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT v FROM settings WHERE k=%s", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default
    except:
        return default

def set_setting(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (k, v) VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE v=%s
    """, (key, value, value))
    conn.commit()
    conn.close()
