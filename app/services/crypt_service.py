import bcrypt


class CryptService:
    def get_password_hash(self, password: str) -> str:
        encoded_password = password.encode("utf-8")
        salt = bcrypt.gensalt()
        bcrypt_hashed = bcrypt.hashpw(encoded_password, salt)
        return bcrypt_hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
