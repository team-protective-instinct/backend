from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr


# 생성할 때 받는 데이터 (비밀번호 포함)
class UserCreate(UserBase):
    password: str


# API 응답으로 보낼 데이터 (비밀번호 제외)
class User(UserBase):
    idx: int
    is_active: bool

    class Config:
        from_attributes = True  # SQLAlchemy 객체를 Pydantic으로 변환 허용


class UserSignIn(UserBase):
    password: str
