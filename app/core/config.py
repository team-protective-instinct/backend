import urllib.parse

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USER: str = Field(default=...)
    DB_PASSWORD: str = Field(default=...)
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=3306)
    DB_NAME: str = Field(default=...)

    # LLM Settings
    LLM_PROVIDER: str = Field(default="gemini")  # "gemini", "anthropic", "openai"
    LLM_MODEL: str = Field(default="gemini-3.1-pro")
    GOOGLE_API_KEY: str | None = Field(default=None)
    ANTHROPIC_API_KEY: str | None = Field(default=None)
    OPENAI_API_KEY: str | None = Field(default=None)
    RAG_EMBEDDING_MODEL: str = Field(default="gemini-embedding-001")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def db_url(self) -> str:
        # Encode the password safely for a database URL.
        # Example: "p@ssword" -> "p%40ssword"
        pwd = urllib.parse.quote_plus(self.DB_PASSWORD)
        return f"postgresql://{self.DB_USER}:{pwd}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
