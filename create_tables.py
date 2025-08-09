from db.models import Base
from db.session import engine

def create_tables():
    Base.metadata.drop_all(bind=engine)  # حذف الجداول القديمة (احذر قبل التشغيل في الإنتاج)
    Base.metadata.create_all(bind=engine)
    print("✅ تم إنشاء الجداول بنجاح.")

if __name__ == "__main__":
    create_tables()
