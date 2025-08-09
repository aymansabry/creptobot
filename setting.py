# settings.py
from database import query, execute

def get_setting(key, default=None):
    r = query("SELECT setting_value FROM settings WHERE setting_key=%s", (key,), fetchone=True)
    if r:
        return r['setting_value']
    return default

def set_setting(key, value):
    existing = query("SELECT id FROM settings WHERE setting_key=%s", (key,), fetchone=True)
    if existing:
        execute("UPDATE settings SET setting_value=%s WHERE setting_key=%s", (value, key))
    else:
        execute("INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s)", (key, value))
