from pydantic import BaseModel, Field


class ElasticsearchSearchInput(BaseModel):
    """Constrained search parameters exposed to the incident analyzer LLM."""

    source_ip: str | None = Field(
        default=None,
        description="Source/client IP address to correlate around the alert.",
    )
    uri: str | None = Field(
        default=None,
        description="HTTP URI/path or URI fragment to correlate.",
    )
    rule_id: str | None = Field(
        default=None,
        description="Security rule identifier from WAF/ElastAlert logs.",
    )
    keyword: str | None = Field(
        default=None,
        description="Small payload or rule-message keyword. Do not use broad wildcards.",
    )
    minutes: int = Field(
        default=10,
        ge=1,
        le=30,
        description="Lookback window in minutes. The backend enforces an upper bound.",
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of compact events to return.",
    )
