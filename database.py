# database.py
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# --- بيانات الاتصال بقاعدة البيانات ---
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "railway"
}

# --- الاتصال بالقاعدة ---
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

# --- إنشاء الجداول إذا لم تكن موجودة ---
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            role VARCHAR(20) DEFAULT 'client',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS exchanges (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            name VARCHAR(50),
            api_key TEXT,
            api_secret TEXT,
            sandbox BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            k VARCHAR(50) PRIMARY KEY,
            v TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS investments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            exchange_name VARCHAR(50),
            amount FLOAT,
            is_virtual BOOLEAN,
            status VARCHAR(20) DEFAULT 'active',
            profit FLOAT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

# --- استرجاع دور المستخدم ---
def get_user_role(telegram_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT role FROM users WHERE telegram_id=%s", (telegram_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row['role'] if row else "client"

# --- حفظ/تحديث إعداد ---
def set_setting(key, value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO settings (k, v) VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE v=%s
    """, (key, value, value))
    conn.commit()
    cur.close()
    conn.close()

# --- قراءة إعداد ---
def get_setting(key, default=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT v FROM settings WHERE k=%s", (key,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row['v'] if row else default

# --- إضافة منصة للمستخدم ---
def add_exchange(user_id, name, api_key, api_secret, sandbox=False):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO exchanges (user_id, name, api_key, api_secret, sandbox)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, name, api_key, api_secret, sandbox))
    conn.commit()
    cur.close()
    conn.close()

# --- استرجاع المنصات للمستخدم ---
def get_user_exchanges(telegram_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT e.name, e.api_key, e.api_secret, e.sandbox
        FROM exchanges e
        JOIN users u ON e.user_id = u.id
        WHERE u.telegram_id = %s
    """, (telegram_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# --- إضافة مستخدم جديد إذا مش موجود ---
def add_user_if_not_exists(telegram_id, role="client"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE telegram_id=%s", (telegram_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (telegram_id, role) VALUES (%s, %s)", (telegram_id, role))
    conn.commit()
    cur.close()
    conn.close()

