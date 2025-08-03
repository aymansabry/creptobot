from datetime import datetime

def current_timestamp():
    return datetime.utcnow().isoformat()
