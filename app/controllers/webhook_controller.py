import logging
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide
from app.services.incident_service import IncidentService
from app.core.container import Container
from app.schemas import (
    LogEntry,
    WebhookAlertRequest,
)
from http import HTTPStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["Webhook - 로그 기반 위협 분석"])

MAX_STORED_TEXT_CHARS = 12000


def _truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}...[truncated {len(value) - max_length} chars]"


def _logs_to_text(logs: list[LogEntry]) -> str:
    """LogEntry 리스트를 에이전트가 소비할 수 있는 텍스트 형태로 변환합니다."""
    parts: list[str] = []
    for i, log in enumerate(logs, 1):
        entry = (
            f"[Log #{i}]\n"
            f"  Time      : {log.timestamp}\n"
            f"  Source IP  : {log.source_ip}\n"
            f"  Method     : {log.method}\n"
            f"  URI        : {log.uri}\n"
            f"  User-Agent : {log.user_agent or 'N/A'}\n"
            f"  Status Code: {log.status_code or 'N/A'}\n"
            f"  Body       : {log.body or 'N/A'}\n"
            f"  Rule ID    : {log.rule_id or 'N/A'}\n"
            f"  Rule Msg   : {log.rule_message or 'N/A'}"
        )
        parts.append(entry)
    return _truncate("\n\n".join(parts), MAX_STORED_TEXT_CHARS)


def _elastalert_to_text(request: WebhookAlertRequest) -> str:
    """ElastAlert 기본 webhook payload를 에이전트 분석용 텍스트로 변환합니다."""
    return (
        "[ElastAlert]\n"
        f"  Title      : {request.title or 'N/A'}\n"
        f"  Rule Name  : {request.rule_name or 'N/A'}\n"
        f"  Alert Name : {request.alert_name}\n"
        f"  Time       : {request.timestamp or 'N/A'}\n"
        f"  Severity   : {request.severity}\n"
        "  Raw Log    :\n"
        f"{request.log_message or 'N/A'}"
    )


@router.post(
    "",
    status_code=HTTPStatus.ACCEPTED,
    summary="알림 접수",
    description=(
        "ElastAlert2 / ModSecurity 등 외부 시스템에서 로그 알림을 수신합니다.\n\n"
        "로그를 incidents 테이블에 저장하고, 별도 worker 가 threat_analyzer_agent 를 실행합니다."
    ),
)
@inject
async def webhook_receive(
    request: WebhookAlertRequest,
    incident_service: IncidentService = Depends(Provide[Container.incident_service]),
):
    alert_name = request.rule_name or request.alert_name
    log_text = _logs_to_text(request.logs) if request.logs else _elastalert_to_text(request)
    log_text = _truncate(log_text, MAX_STORED_TEXT_CHARS)
    incident = incident_service.create_from_webhook(
        title=f"[Webhook] {alert_name}",
        severity=request.severity,
        evidence_logs=log_text,
        raw_payload=request.model_dump(mode="json"),
    )
    logger.info("Webhook incident queued - incident_idx=%s alert=%s", incident.idx, alert_name)
    return {
        "status": "accepted",
        "alert_name": alert_name,
        "incident_idx": incident.idx,
        "log_count": len(request.logs) if request.logs else 1,
    }
