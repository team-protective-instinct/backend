import logging
import time

from app.core.container import Container
from app.services.ai_invoker_service import AiInvokerService
from app.services.incident_service import IncidentService


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class IncidentAgentWorker:
    def __init__(
        self,
        incident_service: IncidentService,
        ai_invoker_service: AiInvokerService,
        batch_size: int = 5,
        poll_interval_seconds: int = 5,
    ):
        self.incident_service = incident_service
        self.ai_invoker_service = ai_invoker_service
        self.batch_size = batch_size
        self.poll_interval_seconds = poll_interval_seconds

    def run_forever(self) -> None:
        logger.info("Incident agent worker started")
        while True:
            try:
                processed_count = self.run_once()
            except Exception:
                logger.exception("Incident agent worker iteration failed")
                time.sleep(self.poll_interval_seconds)
                continue
            if processed_count == 0:
                time.sleep(self.poll_interval_seconds)

    def run_once(self) -> int:
        incidents = self.incident_service.claim_pending_analysis_batch(
            limit=self.batch_size
        )
        for incident in incidents:
            try:
                thread_id, analysis = self.ai_invoker_service.generate_incident_reports(
                    incident.evidence_logs or ""
                )
                self.incident_service.mark_analysis_succeeded(
                    incident_idx=incident.idx,
                    thread_id=thread_id,
                    analysis=analysis,
                )
                logger.info("Incident analysis completed - incident_idx=%s", incident.idx)
            except Exception as exc:
                logger.exception("Incident analysis failed - incident_idx=%s", incident.idx)
                self.incident_service.mark_analysis_failed(incident.idx, exc)
        return len(incidents)


def main() -> None:
    container = Container()
    container.db().create_database()
    worker = IncidentAgentWorker(
        incident_service=container.incident_service(),
        ai_invoker_service=container.ai_invoker_service(),
    )
    worker.run_forever()


if __name__ == "__main__":
    main()
