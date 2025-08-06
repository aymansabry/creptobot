from db.models import Base
from sqlalchemy import create_engine
from core.config import config
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def run_migration():
    try:
        db_params = config.DB_PARAMS
        if not db_params:
            raise ValueError("DATABASE_URL not configured in environment variables")

        connection_string = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
        engine = create_engine(connection_string)
        
        logger.info("⏳ جاري إنشاء الجداول...")
        Base.metadata.create_all(engine)
        logger.info("✅ تم إنشاء الجداول بنجاح!")
    except Exception as e:
        logger.error(f"❌ فشل في تنفيذ الهجرة: {str(e)}")
        raise

if __name__ == '__main__':
    run_migration()
