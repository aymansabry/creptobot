from bots.telegram_bot import main as start_bot
from db.database import init_db

def main():
    # تهيئة قاعدة البيانات
    init_db()
    
    # بدء بوت التليجرام
    start_bot()

if __name__ == '__main__':
    main()