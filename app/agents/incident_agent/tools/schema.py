from pydantic import BaseModel, Field


class ElasticsearchSearchInput(BaseModel):
    """Constrained search parameters exposed to the incident analyzer LLM."""

    max_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="가장 최근 로그 중 수집할 로그의 최대 개수.",
    )
