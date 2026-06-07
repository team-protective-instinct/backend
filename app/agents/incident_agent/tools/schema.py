from pydantic import BaseModel, Field


class ElasticsearchSearchInput(BaseModel):
    """Constrained search parameters exposed to the incident analyzer LLM."""

    alert_timestamp: str | None = Field(
        default=None,
        max_length=128,
        description=(
            "Alert event timestamp from the webhook payload. When provided, "
            "searches logs around this timestamp instead of using now."
        ),
    )
    window_minutes: int | None = Field(
        default=None,
        ge=1,
        le=120,
        description="Minutes before and after alert_timestamp to search.",
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of compact events to return.",
    )
