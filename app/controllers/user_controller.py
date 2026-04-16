import app.services.user_service as user_service
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.user_schema import User, UserCreate, UserSignIn
from app.services.jwt_service import create_access_token

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return user_service.get_users(db, skip=skip, limit=limit)


@router.get("/{user_idx}", response_model=User)
def read_user(user_idx: int, db: Session = Depends(get_db)):
    db_user = user_service.get_user(db, user_idx=user_idx)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.post("/signup")
def sign_up(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = user_service.get_user_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return user_service.create_user(db=db, user=user)


@router.post("/signin")
def sign_in(user: UserSignIn, db: Session = Depends(get_db)):
    hashed_password = user_service.get_hashed_password(db, email=user.email)

    if not user_service.verify_user_password(user.password, hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
