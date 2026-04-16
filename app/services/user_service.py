from sqlalchemy.orm import Session
import app.models.user_model as model
import app.schemas.user_schema as schema
from app.services.crypt_service import get_password_hash, verify_password


def get_user(db: Session, user_idx: int):
    return db.query(model.User).filter(model.User.idx == user_idx).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(model.User).offset(skip).limit(limit).all()


def get_user_by_email(db: Session, email: str):
    return db.query(model.User).filter(model.User.email == email).first()


def get_hashed_password(db: Session, email: str) -> str | None:
    user = get_user_by_email(db, email)
    if user:
        return user.hashed_password
    return None


def verify_user_password(password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return False
    if not verify_password(password, hashed_password):
        return False
    return True


def create_user(db: Session, user: schema.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = model.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_idx: int):
    db_user = db.query(model.User).filter(model.User.idx == user_idx).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user
