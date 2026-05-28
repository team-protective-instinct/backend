import logging
import time

from app.core.container import Container
from app.services.ai_invoker_service import AiInvokerService
from app.services.incident_service import IncidentService
from app.services.incident_raw_log_service import IncidentRawLogService
from app.services.incident_report_service import IncidentReportService
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
        raw_log_service: IncidentRawLogService,
        report_service: IncidentReportService,
        response_plan_service: ResponsePlanService,
        ai_invoker_service: AiInvokerService,
        batch_size: int = 5,
        poll_interval_seconds: int = 5,
    ):
        self.incident_service = incident_service
        self.raw_log_service = raw_log_service
        self.report_service = report_service
        self.response_plan_service = response_plan_service
        self.ai_invoker_service = ai_invoker_service
        self.batch_size = batch_size
        self.poll_interval_seconds = poll_interval_seconds

    def run_forever(self) -> None:
        logger.info("Response plan agent worker started")
        while True:
            try:
                processed_count = self.run_once()
            except Exception:
                logger.exception("Response plan agent worker iteration failed")
                time.sleep(self.poll_interval_seconds)
                continue
            if processed_count == 0:
                time.sleep(self.poll_interval_seconds)

    def run_once(self) -> int:
        incidents = self.incident_service.claim_pending_response_plan_batch(
            limit=self.batch_size
        )
        for incident in incidents:
            try:
                report = self.report_service.get_latest_by_incident(incident.idx)
                if report is None:
                    raise RuntimeError("Incident report not found")
                raw_log = self.raw_log_service.get_latest_by_incident(incident.idx)
                thread_id, draft = (
                    self.ai_invoker_service.generate_incident_response_plan(
                        incident,
                        report,
                        raw_log.evidence_logs if raw_log is not None else "",
                    )
                )
                self.response_plan_service.create_from_draft(
                    incident_idx=incident.idx,
                    thread_id=thread_id,
                    draft=draft,
                )
                self.incident_service.mark_response_plan_succeeded(incident.idx)
                logger.info("Response plan completed - incident_idx=%s", incident.idx)
            except Exception as exc:
                logger.exception("Response plan failed - incident_idx=%s", incident.idx)
                self.incident_service.mark_response_plan_failed(incident.idx, exc)
        return len(incidents)


def main() -> None:
    container = Container()
    container.db().create_database()
    worker = ResponsePlanAgentWorker(
        incident_service=container.incident_service(),
        raw_log_service=container.incident_raw_log_service(),
        report_service=container.incident_report_service(),
        response_plan_service=container.response_plan_service(),
        ai_invoker_service=container.ai_invoker_service(),
    )
    worker.run_forever()


if __name__ == "__main__":
    main()
