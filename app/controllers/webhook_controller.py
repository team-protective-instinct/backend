import logging
from fastapi import APIRouter, BackgroundTasks, Depends
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
    return "\n\n".join(parts)


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


def _run_analysis_background(
    alert_name: str, log_text: str, incident_service: IncidentService
):
    """백그라운드에서 위협 분석을 실행합니다 (비동기 엔드포인트용)."""
    print("\n" + "=" * 50)
    print(f"🚨 [Webhook] 알림 '{alert_name}' 접수 - 백그라운드 분석 시작")
    print("=" * 50)

    try:
        incident_service.incident_analysis(log_text)
        logger.info(f"백그라운드 분석 완료 - alert={alert_name}")
    except Exception:
        logger.exception(f"위협 분석 중 오류 발생 - alert={alert_name}")


@router.post(
    "",
    status_code=HTTPStatus.ACCEPTED,
    summary="알림 접수 (비동기)",
    description=(
        "ElastAlert2 / ModSecurity 등 외부 시스템에서 로그 알림을 수신합니다.\n\n"
        "로그를 접수한 뒤 **백그라운드**에서 threat_analyzer_agent 를 실행하고,\n"
        "즉시 접수 확인 응답을 반환합니다."
    ),
)
@inject
async def webhook_receive(
    request: WebhookAlertRequest,
    background_tasks: BackgroundTasks,
    incident_service: IncidentService = Depends(Provide[Container.incident_service]),
):
    alert_name = request.rule_name or request.alert_name
    log_text = _logs_to_text(request.logs) if request.logs else _elastalert_to_text(request)
    background_tasks.add_task(
        _run_analysis_background, alert_name, log_text, incident_service
    )
    return {
        "status": "accepted",
        "alert_name": alert_name,
        "log_count": len(request.logs) if request.logs else 1,
    }
