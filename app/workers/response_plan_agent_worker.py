import asyncio
import logging

from app.core.container import Container
from app.schemas import ExpoPushMessage
from app.services.ai_invoker_service import AiInvokerService
from app.services.incident_service import IncidentService
from app.services.incident_report_service import IncidentReportService
from app.services.notification_service import NotificationService
from app.services.push_token_service import PushTokenService
from app.services.response_plan_service import ResponsePlanService


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# TODO: `batch_size`는 환경변수로 관리하도록 수정하기
class ResponsePlanAgentWorker:
    def __init__(
        self,
        incident_service: IncidentService,
        report_service: IncidentReportService,
        response_plan_service: ResponsePlanService,
        ai_invoker_service: AiInvokerService,
        push_token_service: PushTokenService,
        notification_service: NotificationService,
        batch_size: int = 5,
        poll_interval_seconds: int = 5,
    ):
        self.incident_service = incident_service
        self.report_service = report_service
        self.response_plan_service = response_plan_service
        self.ai_invoker_service = ai_invoker_service
        self.push_token_service = push_token_service
        self.push_notification_service = notification_service
        self.batch_size = batch_size
        self.poll_interval_seconds = poll_interval_seconds

    async def run_forever(self) -> None:
        logger.info("Response plan agent worker started")
        while True:
            try:
                processed_count = await self.run_once()
            except Exception:
                logger.exception("Response plan agent worker iteration failed")
                await asyncio.sleep(self.poll_interval_seconds)
                continue
            if processed_count == 0:
                await asyncio.sleep(self.poll_interval_seconds)

    async def run_once(self) -> int:
        incidents = self.incident_service.claim_pending_response_plan_batch(
            limit=self.batch_size
        )
        for incident in incidents:
            try:
                report = self.report_service.get_latest_by_incident(incident.idx)
                if report is None:
                    raise RuntimeError("Incident report not found")
                (
                    thread_id,
                    generation_result,
                ) = await self.ai_invoker_service.generate_incident_response_plan(
                    incident,
                    report,
                )
                response_plan = (
                    self.response_plan_service.create_from_generation_result(
                        incident_idx=incident.idx,
                        thread_id=thread_id,
                        generation_result=generation_result,
                    )
                )
                self.incident_service.mark_response_plan_succeeded(incident.idx)
                try:
                    await self._send_response_plan_completed_notification(
                        incident_idx=incident.idx,
                        response_plan_idx=response_plan.idx,
                    )
                except Exception:
                    logger.exception(
                        "Response plan push notification failed - incident_idx=%s response_plan_idx=%s",
                        incident.idx,
                        response_plan.idx,
                    )
                logger.info("Response plan completed - incident_idx=%s", incident.idx)
            except Exception as exc:
                logger.exception("Response plan failed - incident_idx=%s", incident.idx)
                self.incident_service.mark_response_plan_failed(incident.idx, exc)
        return len(incidents)

    async def _send_response_plan_completed_notification(
        self,
        incident_idx: int,
        response_plan_idx: int,
    ) -> None:
        if not self.push_notification_service.settings.EXPO_PUSH_ENABLED:
            logger.info("Expo push disabled; skipping response plan notification")
            return

        push_tokens = self.push_token_service.list_active_expo_tokens()
        if not push_tokens:
            logger.info(
                "No active Expo push tokens; skipping response plan notification"
            )
            return

        incident_idx_text = str(incident_idx)
        messages = [
            ExpoPushMessage(
                to=push_token.token,
                title="Response plan complete",
                body="A response plan is ready for review.",
                data={
                    "type": "response_plan_completed",
                    "incident_idx": incident_idx_text,
                    "response_plan_idx": str(response_plan_idx),
                    "url": f"/incidents/{incident_idx_text}",
                },
            )
            for push_token in push_tokens
        ]
        await self.push_notification_service.send_notification(messages)


async def main() -> None:
    container = Container()
    container.db().create_database()
    await container.response_plan_agent().initialize()
    try:
        worker = ResponsePlanAgentWorker(
            incident_service=container.incident_service(),
            report_service=container.incident_report_service(),
            response_plan_service=container.response_plan_service(),
            ai_invoker_service=container.ai_invoker_service(),
            push_token_service=container.push_token_service(),
            notification_service=container.notification_service(),
        )
        await worker.run_forever()
    finally:
        await container.response_plan_agent().aclose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Response plan agent worker stopped")
