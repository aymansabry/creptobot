from sqlmodel import SQLModel, create_engine
import os

# استخدم SQLite - سيتم إنشاء ملف قاعدة البيانات في نفس مجلد المشروع
DATABASE_URL = "sqlite:///database.db"

engine = create_engine(DATABASE_URL, echo=False)

async def create_db_and_tables():
    import bot.models  # تأكد من استيراد جميع النماذج
    SQLModel.metadata.create_all(engine)
