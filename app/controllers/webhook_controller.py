import logging
from fastapi import APIRouter, BackgroundTasks
from app.services.incident_service import incident_analysis
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


def _run_analysis_background(alert_name: str, log_text: str):
    """백그라운드에서 위협 분석을 실행합니다 (비동기 엔드포인트용)."""
    print("\n" + "=" * 50)
    print(f"🚨 [Webhook] 알림 '{alert_name}' 접수 - 백그라운드 분석 시작")
    print("=" * 50)

    try:
        incident_analysis(log_text)
        logger.info(f"백그라운드 분석 완료 - alert={alert_name}")
    except Exception:
        logger.exception(f"위협 분석 중 오류 발생 - alert={alert_name}")


@router.post(
    "/",
    status_code=HTTPStatus.ACCEPTED,
    summary="알림 접수 (비동기)",
    description=(
        "ElastAlert2 / ModSecurity 등 외부 시스템에서 로그 알림을 수신합니다.\n\n"
        "로그를 접수한 뒤 **백그라운드**에서 threat_analyzer_agent 를 실행하고,\n"
        "즉시 접수 확인 응답을 반환합니다."
    ),
)
async def webhook_receive(
    request: WebhookAlertRequest,
    background_tasks: BackgroundTasks,
):
    log_text = _logs_to_text(request.logs)
    background_tasks.add_task(_run_analysis_background, request.alert_name, log_text)
