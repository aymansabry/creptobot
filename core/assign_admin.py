# assign_admin.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import User
from core.config import DATABASE_URL

def assign_admin(telegram_id: 5427885291):
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.is_admin = True
        session.commit()
        print(f"✅ تم تعيين المستخدم {telegram_id} كمدير.")
    else:
        print(f"❌ المستخدم بالـ telegram_id={telegram_id} غير موجود في قاعدة البيانات.")

if __name__ == "__main__":
    telegram_id_input = input("أدخل رقم تليجرام للمستخدم لتعيينه مدير: ")
    assign_admin(telegram_id_input)

