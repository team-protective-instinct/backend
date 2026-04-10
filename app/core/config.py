import urllib.parse
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USER: str = Field(default=...)
    DB_PASSWORD: str = Field(default=...)
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=3306)
    DB_NAME: str = Field(default=...)

    GOOGLE_API_KEY: str = Field(default=...)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # .env에 클래스에 없는 변수가 있어도 무시
    )

    # .env 파일을 읽어오기 위한 설정
    model_config = SettingsConfigDict(env_file=".env")

    @property
    def db_url(self) -> str:
        # 패스워드를 URL 안전하게 인코딩합니다.
        # 예: 'p@ssword' -> 'p%40ssword'
        encoded_password = urllib.parse.quote_plus(self.DB_PASSWORD)
        return f"mysql+pymysql://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
