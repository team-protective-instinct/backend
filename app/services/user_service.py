from sqlalchemy.orm import Session
import app.models.user_model as model
import app.schemas.user_schema as schema


def get_user(db: Session, user_idx: int):
    return db.query(model.User).filter(model.User.idx == user_idx).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(model.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schema.UserCreate):
    # 실제 프로젝트에선 passlib 등으로 해싱해야 하지만, 일단 연습용으로 그대로 저장
    db_user = model.User(email=user.email, hashed_password=user.password)
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
