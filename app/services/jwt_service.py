import jwt
from datetime import datetime, timedelta
from app.core.config import settings


def create_access_token(
    data: dict,
):
    to_encode = data.copy()
    acess_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": datetime.utcnow() + acess_token_expires})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt
