# utils/logger.py
from database.connection import get_connection

def log_action(user_id, action, details=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)", (user_id, action, details))
    conn.commit()
    conn.close()