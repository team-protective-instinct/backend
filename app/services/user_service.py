from typing import Optional, List, Callable
from sqlalchemy.orm import Session
from app.models import User
from app.schemas import UserCreate
from .crypt_service import CryptService


class UserService:
    def __init__(
        self, 
        session_factory: Callable[..., Session], 
        crypt_service: CryptService
    ):
        self.session_factory = session_factory
        self.crypt_service = crypt_service

    def get_user(self, user_idx: int) -> Optional[User]:
        with self.session_factory() as db:
            return db.query(User).filter(User.idx == user_idx).first()

    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        with self.session_factory() as db:
            return db.query(User).offset(skip).limit(limit).all()

    def get_user_by_email(self, email: str) -> Optional[User]:
        with self.session_factory() as db:
            return db.query(User).filter(User.email == email).first()

    def create_user(self, user: UserCreate) -> User:
        hashed_password = self.crypt_service.get_password_hash(user.password)
        with self.session_factory() as db:
            db_user = User(email=user.email, hashed_password=hashed_password)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user

    def delete_user(self, user_idx: int) -> Optional[User]:
        with self.session_factory() as db:
            db_user = db.query(User).filter(User.idx == user_idx).first()
            if db_user:
                db.delete(db_user)
                db.commit()
            return db_user

    def get_hashed_password(self, email: str) -> Optional[str]:
        user = self.get_user_by_email(email)
        if user:
            return user.hashed_password
        return None

    def verify_user_password(self, password: str, hashed_password: Optional[str]) -> bool:
        if not hashed_password:
            return False
        return self.crypt_service.verify_password(password, hashed_password)
