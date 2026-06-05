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

    # Elasticsearch MCP log search settings
    ELASTICSEARCH_MCP_ENABLED: bool = Field(default=False)
    ELASTICSEARCH_MCP_URL: str = Field(default="http://localhost:8085/mcp")
    ELASTICSEARCH_MCP_ALLOWED_INDEX_PATTERN: str = Field(default="logstash-*")
    ELASTICSEARCH_MCP_SERVICE_FIELD: str = Field(default="fields.service")
    ELASTICSEARCH_MCP_SERVICE_VALUE: str = Field(default="dvwa-apache")
    ELASTICSEARCH_MCP_MAX_RESULTS: int = Field(default=20)
    ELASTICSEARCH_MCP_MAX_WINDOW_MINUTES: int = Field(default=30)
    ELASTICSEARCH_MCP_REQUEST_TIMEOUT_SECONDS: int = Field(default=10)

    # Victim MCP settings for response-plan enrichment and future execution.
    VICTIM_MCP_ENABLED: bool = Field(default=False)
    VICTIM_MCP_URL: str = Field(default="http://localhost:9001/mcp")
    VICTIM_MCP_REQUEST_TIMEOUT_SECONDS: int = Field(default=10)
    VICTIM_MCP_MAX_RESULT_CHARS: int = Field(default=6000)

    # Expo Push Service settings for SOC mobile notifications.
    EXPO_PUSH_ENABLED: bool = Field(default=True)
    EXPO_PUSH_URL: str = Field(default="https://exp.host/--/api/v2/push/send")
    EXPO_PUSH_ACCESS_TOKEN: str | None = Field(default=None)
    EXPO_PUSH_REQUEST_TIMEOUT_SECONDS: int = Field(default=10)

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
