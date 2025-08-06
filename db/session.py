from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from time import sleep

DB_RETRIES = 3
DB_DELAY = 5

def get_engine():
    for i in range(DB_RETRIES):
        try:
            engine = create_engine(
                os.getenv("DATABASE_URL"),
                pool_pre_ping=True,
                connect_args={
                    "keepalives": 1,
                    "keepalives_idle": 30,
                    "keepalives_interval": 10,
                    "keepalives_count": 5
                }
            )
            # اختبار الاتصال
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return engine
        except Exception as e:
            if i == DB_RETRIES - 1:
                raise
            sleep(DB_DELAY)

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
