from sqlalchemy import create_engine
from models import Base, User  # نستدعي Base و User من models.py

# بيانات الاتصال بقاعدة البيانات
DB_URL = "mysql+pymysql://USER:PASSWORD@HOST/DATABASE"

# أنشئ محرك الاتصال
engine = create_engine(DB_URL)

def reset_database():
    print("[*] Dropping 'users' table if it exists...")
    Base.metadata.drop_all(bind=engine, tables=[User.__table__])
    
    print("[*] Creating 'users' table...")
    Base.metadata.create_all(bind=engine, tables=[User.__table__])
    
    print("[✔] Database has been reset successfully.")

if __name__ == "__main__":
    reset_database()
