import logging
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide
from app.services.incident_service import IncidentService
from app.core.container import Container
from app.schemas import WebhookAlertRequest
from http import HTTPStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["Webhook - 로그 기반 위협 분석"])

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
    incident = incident_service.create_from_webhook(
        title=f"[Webhook] {alert_name}",
        severity=request.severity,
        raw_payload=request.model_dump(mode="json"),
    )
    logger.info("Webhook incident queued - incident_idx=%s alert=%s", incident.idx, alert_name)
    return {
        "status": "accepted",
        "alert_name": alert_name,
        "incident_idx": incident.idx,
        "log_count": len(request.logs) if request.logs else 1,
    }
