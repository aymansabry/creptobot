from db.models import Base
from db.postgres import engine

def run_migration():
    Base.metadata.create_all(bind=engine)
    print("تم إنشاء الجداول بنجاح!")

if __name__ == '__main__':
    run_migration()
