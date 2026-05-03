from dataclasses import dataclass
from app.models import Incident


@dataclass(frozen=True)  # read-only
class IncidentListResult:
    items: list[Incident]
    page: int
    limit: int
    total: int
    total_pages: int


@dataclass(frozen=True)
class IncidentSummaryResult:
    pending_count: int
    today_count: int
    resolved_count: int
    recent_pending: list[Incident]
