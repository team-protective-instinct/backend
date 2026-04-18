from enum import Enum
from typing import Dict, Optional, TypedDict

from app.core.config import settings


class ProviderType(str, Enum):
    GEMINI = "gemini"
    CLAUDE = "claude"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GPT = "gpt"


# 각 프로바이더별 메타데이터를 구조화하여 관리
class ProviderMetadata(TypedDict):
    langchain_provider: str
    api_key: Optional[str]
    env_var_name: str


# 설정 테이블 정의
PROVIDER_MAP: Dict[str, ProviderMetadata] = {
    ProviderType.GEMINI: {
        "langchain_provider": "google_genai",
        "api_key": settings.GOOGLE_API_KEY,
        "env_var_name": "GOOGLE_API_KEY",
    },
    ProviderType.ANTHROPIC: {
        "langchain_provider": "anthropic",
        "api_key": settings.ANTHROPIC_API_KEY,
        "env_var_name": "ANTHROPIC_API_KEY",
    },
    ProviderType.CLAUDE: {  # 별칭 처리
        "langchain_provider": "anthropic",
        "api_key": settings.ANTHROPIC_API_KEY,
        "env_var_name": "ANTHROPIC_API_KEY",
    },
    ProviderType.OPENAI: {
        "langchain_provider": "openai",
        "api_key": settings.OPENAI_API_KEY,
        "env_var_name": "OPENAI_API_KEY",
    },
    ProviderType.GPT: {  # 별칭 처리
        "langchain_provider": "openai",
        "api_key": settings.OPENAI_API_KEY,
        "env_var_name": "OPENAI_API_KEY",
    },
}
