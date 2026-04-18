import os
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from app.core.config import settings
from app.core.llm_provider import PROVIDER_MAP, ProviderType


def get_llm(temperature: float = 0.7) -> BaseChatModel:
    """
    환경변수 설정에 따라 적절한 LangChain LLM 인스턴스를 반환합니다.
    """

    user_provider = settings.LLM_PROVIDER.lower()

    if user_provider not in PROVIDER_MAP:
        supported = ", ".join([p.value for p in ProviderType])
        raise ValueError(
            f"지원하지 않는 LLM_PROVIDER 입니다: {user_provider}. (지원: {supported})"
        )

    metadata = PROVIDER_MAP[user_provider]

    # API 키를 환경 변수에 동적으로 주입
    if metadata["api_key"]:
        os.environ[metadata["env_var_name"]] = metadata["api_key"]
    else:
        raise ValueError(
            f"{metadata['env_var_name']} 가 .env 파일에 설정되어 있지 않습니다."
        )

    return init_chat_model(
        model=settings.LLM_MODEL,
        model_provider=metadata["langchain_provider"],
        temperature=temperature,
    )
