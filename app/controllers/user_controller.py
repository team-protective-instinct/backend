from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import app.core.database as database
import app.services.user_service as user_service
import app.schemas.user_schema as user_schema

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=user_schema.User)
def create_user(user: user_schema.UserCreate, db: Session = Depends(database.get_db)):
    return user_service.create_user(db=db, user=user)


@router.get("/", response_model=List[user_schema.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return user_service.get_users(db, skip=skip, limit=limit)


@router.get("/{user_idx}", response_model=user_schema.User)
def read_user(user_idx: int, db: Session = Depends(database.get_db)):
    db_user = user_service.get_user(db, user_idx=user_idx)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
