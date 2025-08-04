async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        session = get_db_session()
        
        # تحقق إذا كان المستخدم مسجلاً بالفعل
        existing_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        if not existing_user:
            new_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name if user.last_name else None  # جعلها اختيارية
            )
            
            session.add(new_user)
            session.commit()
            logger.info(f"تم تسجيل مستخدم جديد: {user.id}")
        
        await update.message.reply_text(
            "مرحباً بك! اختر من القائمة:",
            reply_markup=create_main_menu()
        )
        
    except Exception as e:
        logger.error(f"خطأ في التسجيل: {e}")
        await update.message.reply_text("حدث خطأ في النظام، يرجى المحاولة لاحقاً")
        
    finally:
        session.close()
