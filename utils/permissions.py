# معرفات المديرين
ADMINS = [123456789]  # استبدل بمعرفك

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def is_support(user_id: int) -> bool:
    # يمكن توسيعها لاحقًا لتمييز موظفي الدعم
    return user_id in ADMINS  # مبدئيًا نفس المدراء
