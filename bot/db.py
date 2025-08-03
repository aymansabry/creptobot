import sqlalchemy
from sqlmodel import SQLModel, create_engine, Session

from bot.models import User

engine = create_engine(os.getenv("DATABASE_URL"))

async def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
