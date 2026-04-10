from sqlalchemy import Column, Integer, Boolean, String
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    idx = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
