from bots.telegram_bot import main as start_bot
from db.database import init_db

if __name__ == '__main__':
    init_db()
    start_bot()