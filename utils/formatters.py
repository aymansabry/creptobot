from datetime import datetime

def format_usdt(amount):
    return f"{amount:,.2f} USDT"

def format_date(dt: datetime):
    return dt.strftime("%Y-%m-%d %H:%M")
