# migrate_db.py
import sqlite3

def ensure_table(cursor, name, schema):
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {name} ({schema})")

def ensure_column(cursor, table, column, col_type):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [info[1] for info in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

def migrate():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # جدول المستخدمين
    ensure_table(cursor, "users", """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id BIGINT UNIQUE,
        username TEXT,
        plan TEXT DEFAULT 'safe',
        balance REAL DEFAULT 0.0
    """)

    # جدول الاستثمارات
    ensure_table(cursor, "investments", """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        type TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    """)

    # جدول الأرباح
    ensure_table(cursor, "profits", """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        type TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    """)

    # جدول إعدادات المدير
    ensure_table(cursor, "admin_settings", """
        id INTEGER PRIMARY KEY DEFAULT 1,
        bot_share_percent REAL DEFAULT 10.0,
        wallet_address TEXT,
        auto_invest REAL DEFAULT 0.0
    """)
    ensure_column(cursor, "admin_settings", "wallet_address", "TEXT")
    ensure_column(cursor, "admin_settings", "bot_share_percent", "REAL")
    ensure_column(cursor, "admin_settings", "auto_invest", "REAL")

    # سجل النشاط
    ensure_table(cursor, "logs", """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        details TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    """)

    conn.commit()
    conn.close()