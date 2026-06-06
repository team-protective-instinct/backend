from pydantic import BaseModel, Field


class ElasticsearchSearchInput(BaseModel):
    """Constrained search parameters exposed to the incident analyzer LLM."""

    max_results: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of compact events to return.",
    )
