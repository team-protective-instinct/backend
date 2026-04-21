from fastapi import APIRouter, Depends, HTTPException
from typing import List
from dependency_injector.wiring import inject, Provide

from app.schemas import User, UserCreate, UserSignIn
from app.services.user_service import UserService
from app.services.jwt_service import JWTService
from app.core.container import Container

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[User])
@inject
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    user_service: UserService = Depends(Provide[Container.user_service])
):
    return user_service.get_users(skip=skip, limit=limit)


@router.get("/{user_idx}", response_model=User)
@inject
def read_user(
    user_idx: int, 
    user_service: UserService = Depends(Provide[Container.user_service])
):
    db_user = user_service.get_user(user_idx=user_idx)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.post("/signup")
@inject
def sign_up(
    user: UserCreate, 
    user_service: UserService = Depends(Provide[Container.user_service])
):
    existing_user = user_service.get_user_by_email(email=user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return user_service.create_user(user=user)


@router.post("/signin")
@inject
def sign_in(
    user: UserSignIn, 
    user_service: UserService = Depends(Provide[Container.user_service]),
    jwt_service: JWTService = Depends(Provide[Container.jwt_service])
):
    hashed_password = user_service.get_hashed_password(email=user.email)

    if not user_service.verify_user_password(user.password, hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = jwt_service.create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
