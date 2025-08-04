import pytest
from core.database import db, User

class TestDatabase:
    def test_user_creation(self):
        session = db.get_session()
        try:
            user = User(telegram_id=123, first_name="Test")
            session.add(user)
            session.commit()
            
            retrieved = session.query(User).filter_by(telegram_id=123).first()
            assert retrieved is not None
            assert retrieved.first_name == "Test"
            
        finally:
            session.rollback()
            session.close()
