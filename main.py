from db.session import engine, Base
import time
from sqlalchemy import exc

def initialize_db():
    retries = 5
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            return True
        except exc.OperationalError:
            retries -= 1
            time.sleep(5)
    raise Exception("Failed to connect to database after multiple attempts")

if __name__ == '__main__':
    if initialize_db():
        from aiogram import executor
        executor.start_polling(dp, skip_updates=True)
