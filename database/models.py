from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import BigInteger, String, Float

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)