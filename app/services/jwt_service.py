import jwt
from datetime import datetime, timedelta
from app.core.config import Settings


class JWTService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def create_access_token(self, data: dict):
        to_encode = data.copy()
        access_token_expires = timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": datetime.utcnow() + access_token_expires})
        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.SECRET_KEY,
            algorithm=self.settings.ALGORITHM,
        )
        return encoded_jwt
