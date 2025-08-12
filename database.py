# database.py
import os
from urllib.parse import urlparse
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

def parse_database_url(url):
    result = urlparse(url)
    return {
        "host": result.hostname,
        "user": result.username,
        "password": result.password,
        "database": result.path.lstrip("/"),
        "port": int(result.port) if result.port else 3306,
        "auth_plugin": "mysql_native_password",
    }

db_config = parse_database_url(DATABASE_URL)

def get_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as e:
        print("DB connection error:", e)
        return None

def init_database():
    conn = get_connection()
    if not conn:
        raise RuntimeError("Cannot connect to DB")
    cur = conn.cursor()
    # users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        telegram_id BIGINT UNIQUE NOT NULL,
        balance FLOAT DEFAULT 0,
        invested_amount FLOAT DEFAULT 0,
        profit_total FLOAT DEFAULT 0,
        is_investing BOOLEAN DEFAULT FALSE,
        last_active DATETIME NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # platforms (supports test keys)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS platforms (
        id INT AUTO_INCREMENT PRIMARY KEY,
        telegram_id BIGINT NOT NULL,
        platform_name VARCHAR(50) NOT NULL,
        api_key TEXT,
        api_secret TEXT,
        password TEXT,
        api_key_test TEXT,
        api_secret_test TEXT,
        is_sandbox BOOLEAN DEFAULT FALSE,
        enabled BOOLEAN DEFAULT TRUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_platform_user (telegram_id, platform_name)
    )
    """)
    # investments
    cur.execute("""
    CREATE TABLE IF NOT EXISTS investments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        telegram_id BIGINT NOT NULL,
        platform VARCHAR(50),
        type ENUM('virtual','real') NOT NULL,
        amount FLOAT,
        buy_symbol VARCHAR(50),
        sell_symbol VARCHAR(50),
        buy_price FLOAT,
        sell_price FLOAT,
        gross_profit FLOAT,
        net_profit FLOAT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # analysis
    cur.execute("""
    CREATE TABLE IF NOT EXISTS market_analysis (
        id INT AUTO_INCREMENT PRIMARY KEY,
        analysis_text TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # settings
    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        k VARCHAR(64) PRIMARY KEY,
        v TEXT
    )
    """)
    # default bot fee
    cur.execute("SELECT v FROM settings WHERE k='bot_fee_percent'")
    if not cur.fetchone():
        cur.execute("INSERT INTO settings (k,v) VALUES (%s,%s)", ("bot_fee_percent","10"))
    conn.commit()
    cur.close()
    conn.close()

# ---------------- helper blocking DB functions ----------------

def ensure_user(telegram_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT IGNORE INTO users (telegram_id) VALUES (%s)", (telegram_id,))
    conn.commit()
    cur.close()
    conn.close()

def update_last_active(telegram_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET last_active = NOW() WHERE telegram_id=%s", (telegram_id,))
    conn.commit()
    cur.close()
    conn.close()

def set_user_balance(telegram_id, amount):
    ensure_user(telegram_id)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance=%s WHERE telegram_id=%s", (amount, telegram_id))
    conn.commit()
    cur.close()
    conn.close()

def get_user_balance(telegram_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE telegram_id=%s", (telegram_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return float(row[0]) if row and row[0] is not None else 0.0

def add_or_update_platform(telegram_id, platform_name,
                           api_key=None, api_secret=None, password=None,
                           api_key_test=None, api_secret_test=None, is_sandbox=False):
    ensure_user(telegram_id)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO platforms (telegram_id, platform_name, api_key, api_secret, password, api_key_test, api_secret_test, is_sandbox)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE api_key=VALUES(api_key), api_secret=VALUES(api_secret), password=VALUES(password),
                                api_key_test=VALUES(api_key_test), api_secret_test=VALUES(api_secret_test), is_sandbox=VALUES(is_sandbox), enabled=1
    """, (telegram_id, platform_name, api_key, api_secret, password, api_key_test, api_secret_test, 1 if is_sandbox else 0))
    conn.commit()
    cur.close()
    conn.close()

def set_platform_enabled(telegram_id, platform_name, enabled: bool):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE platforms SET enabled=%s WHERE telegram_id=%s AND platform_name=%s", (1 if enabled else 0, telegram_id, platform_name))
    conn.commit()
    cur.close()
    conn.close()

def get_platforms(telegram_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT platform_name, api_key, api_secret, password, api_key_test, api_secret_test, is_sandbox, enabled FROM platforms WHERE telegram_id=%s", (telegram_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows or []

def get_platform_by_name(telegram_id, platform_name):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT platform_name, api_key, api_secret, password, api_key_test, api_secret_test, is_sandbox, enabled FROM platforms WHERE telegram_id=%s AND platform_name=%s", (telegram_id, platform_name))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def log_investment(telegram_id, platform, inv_type, amount, buy_symbol, sell_symbol, buy_price, sell_price, gross_profit, net_profit):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO investments (telegram_id, platform, type, amount, buy_symbol, sell_symbol, buy_price, sell_price, gross_profit, net_profit)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (telegram_id, platform, inv_type, amount, buy_symbol, sell_symbol, buy_price, sell_price, gross_profit, net_profit))
    conn.commit()
    cur.close()
    conn.close()

def get_investments_sum_since(telegram_id, start_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT SUM(net_profit) FROM investments WHERE telegram_id=%s AND timestamp >= %s", (telegram_id, start_date))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return float(row[0]) if row and row[0] is not None else 0.0

def get_total_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return int(row[0]) if row else 0

def get_online_users(minutes=10):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE last_active >= (NOW() - INTERVAL %s MINUTE)", (minutes,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return int(row[0]) if row else 0

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
    cur.execute("INSERT INTO settings (k,v) VALUES (%s,%s) ON DUPLICATE KEY UPDATE v=VALUES(v)", (key, str(value)))
    conn.commit()
    cur.close()
    conn.close()
