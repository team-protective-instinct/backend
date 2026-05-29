from datetime import datetime
from typing import Literal, TYPE_CHECKING

from enum import Enum
from pydantic import BaseModel, Field

from app.dtos import IncidentSummaryResult

if TYPE_CHECKING:
    from app.models import Incident, IncidentRawLog, IncidentReport, ResponsePlan
    from app.schemas.agent_schema import IndicatorEvaluation

from app.schemas.response_plan_schema import ResponsePlanResponse


class SeverityFilter(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


Severity = Literal["critical", "high", "medium", "low"]
IncidentStatus = Literal[
    "analyzing",
    "pending_review",
    "resolved",
    "dismissed",
]


class IncidentKeyIndicatorResponse(BaseModel):
    label: str
    value: bool
    description: str

    @classmethod
    def from_indicator_evaluation(
        cls, indicator: "IndicatorEvaluation"
    ) -> "IncidentKeyIndicatorResponse":
        label = indicator.name.replace("_", " ").title()
        return cls(
            label=label,
            value=indicator.is_detected,
            description=indicator.reasoning,
        )


class IncidentListItemResponse(BaseModel):
    idx: int
    attack_type: str
    severity: Severity
    confidence_score: float
    status: IncidentStatus
    targetIp: str
    targetName: str
    detectedAt: datetime
    created_at: datetime

    @classmethod
    def from_incident(
        cls, incident: "Incident", report: "IncidentReport | None" = None
    ) -> "IncidentListItemResponse":
        return cls(
            idx=incident.idx,
            attack_type=report.attack_type
            if report and report.attack_type
            else "Unknown",
            severity=cls._normalize_severity(incident.severity),
            confidence_score=report.confidence_score
            if report is not None and report.confidence_score is not None
            else 0.0,
            status=cls._normalize_status(incident.status),
            targetIp="192.168.1.50",
            targetName="Web Server (Victim)",
            detectedAt=incident.created_at,
            created_at=incident.created_at,
        )

    @staticmethod
    def _normalize_severity(value: str | None) -> Severity:
        if value in ("critical", "high", "medium", "low"):
            return value  # type: ignore
        return "low"

    @staticmethod
    def _normalize_status(value: str | None) -> IncidentStatus:
        valid_statuses = ("analyzing", "pending_review", "resolved", "dismissed")
        if value in valid_statuses:
            return value  # type: ignore
        return "analyzing"


class IncidentDetailResponse(BaseModel):
    idx: int
    attack_type: str
    severity: str
    confidence_score: float
    status: str
    targetIp: str
    targetName: str
    detectedAt: datetime
    created_at: datetime
    attack_ip: str | None = None
    target_uris: list[str] = Field(default_factory=list)
    suspicious_payloads: list[str] = Field(default_factory=list)
    analysis_summary: str
    key_indicators: list[IncidentKeyIndicatorResponse] = Field(default_factory=list)
    raw_log: str
    response_plan: ResponsePlanResponse | None = None

    @classmethod
    def from_incident(
        cls,
        incident: "Incident",
        report: "IncidentReport | None" = None,
        raw_log: "IncidentRawLog | None" = None,
        response_plan: "ResponsePlan | None" = None,
    ) -> "IncidentDetailResponse":
        analysis = (
            report.analysis_result
            if report is not None and isinstance(report.analysis_result, dict)
            else {}
        )

        key_indicators: list[IncidentKeyIndicatorResponse] = []
        raw_key_indicators = analysis.get("key_indicators")
        if isinstance(raw_key_indicators, list):
            for indicator_data in raw_key_indicators:
                if isinstance(indicator_data, dict):
                    try:
                        from app.schemas.agent_schema import IndicatorEvaluation

                        indicator = IndicatorEvaluation.model_validate(indicator_data)
                        key_indicators.append(
                            IncidentKeyIndicatorResponse.from_indicator_evaluation(
                                indicator
                            )
                        )
                    except Exception:
                        continue

        severity_str = incident.severity or "low"

        attack_ip = analysis.get("attack_ip")
        attack_ip_str: str | None = (
            str(attack_ip)
            if isinstance(attack_ip, (str, int))
            else report.attacker_ip
            if report is not None
            else None
        )

        target_uris_data = analysis.get("target_uris")
        target_uris: list[str] = (
            target_uris_data if isinstance(target_uris_data, list) else []
        )

        suspicious_payloads_data = analysis.get("suspicious_payloads")
        suspicious_payloads: list[str] = (
            suspicious_payloads_data
            if isinstance(suspicious_payloads_data, list)
            else []
        )

        return cls(
            idx=incident.idx,
            attack_type=report.attack_type
            if report and report.attack_type
            else "Unknown",
            severity=severity_str,
            confidence_score=report.confidence_score
            if report is not None and report.confidence_score is not None
            else 0.0,
            status=incident.status or "analyzing",
            targetIp="192.168.1.50",
            targetName="Web Server (Victim)",
            detectedAt=incident.created_at,
            created_at=incident.created_at,
            attack_ip=attack_ip_str,
            target_uris=target_uris,
            suspicious_payloads=suspicious_payloads,
            analysis_summary=report.analysis_summary
            if report and report.analysis_summary
            else "",
            key_indicators=key_indicators,
            raw_log=raw_log.evidence_logs if raw_log is not None else "",
            response_plan=ResponsePlanResponse.from_response_plan(response_plan)
            if response_plan is not None
            else None,
        )


class IncidentListResponse(BaseModel):
    items: list[IncidentListItemResponse]
    page: int
    limit: int
    total: int
    total_pages: int


class OverviewSummaryResponse(BaseModel):
    pending_count: int
    today_count: int
    resolved_count: int
    recent_pending: list[IncidentListItemResponse]

    @classmethod
    def from_incident_summary(
        cls, incident: IncidentSummaryResult
    ) -> "OverviewSummaryResponse":
        recent_pending = [
            IncidentListItemResponse.from_incident(recent.incident, recent.report)
            for recent in incident.recent_pending
        ]

        return cls(
            pending_count=incident.pending_count,
            today_count=incident.today_count,
            resolved_count=incident.resolved_count,
            recent_pending=recent_pending,
        )
