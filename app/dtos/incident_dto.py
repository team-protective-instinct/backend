from dataclasses import dataclass
from app.models import Incident, IncidentReport


@dataclass(frozen=True)
class IncidentWithReport:
    incident: Incident
    report: IncidentReport | None


@dataclass(frozen=True)  # read-only
class IncidentListResult:
    items: list[IncidentWithReport]
    page: int
    limit: int
    total: int
    total_pages: int


@dataclass(frozen=True)
class IncidentSummaryResult:
    pending_count: int
    today_count: int
    resolved_count: int
    recent_pending: list[IncidentWithReport]
