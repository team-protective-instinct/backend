import json
import logging
import uuid
from typing import Optional, List, Callable
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session
from app.models import Incident
from app.agents.incident_analyzer.state import AgentState
from app.agents.incident_analyzer.prompt import LOG_ANALYSIS_REQUEST_PREFIX
from app.agents.incident_analyzer.agent import ThreatAnalyzerAgent


logger = logging.getLogger(__name__)


class IncidentService:
    def __init__(
        self, 
        session_factory: Callable[..., Session],
        threat_agent: ThreatAnalyzerAgent
    ):
        self.session_factory = session_factory
        self.threat_agent = threat_agent

    def create_incident(self, title: str, description: str) -> Incident:
        with self.session_factory() as db:
            incident = Incident(title=title, description=description)
            db.add(incident)
            db.commit()
            db.refresh(incident)
            return incident

    def create_incident_from_analysis(
        self,
        db: Session,
        title: str,
        raw_log: str,
        analysis_data: dict | None,
        is_threat: bool,
        thread_id: str,
    ) -> Incident:
        incident = Incident(
            thread_id=thread_id,
            title=title,
            status="completed",
            evidence_logs=raw_log,
            analysis_result=analysis_data,
            is_identified_threat=is_threat,
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    def get_pending_incidents(self) -> List[Incident]:
        with self.session_factory() as db:
            return db.query(Incident).filter(Incident.status == "pending").all()

    def get_incident_by_idx(self, incident_idx: int) -> Optional[Incident]:
        with self.session_factory() as db:
            return db.query(Incident).filter(Incident.idx == incident_idx).first()

    def approve_incident(self, incident_id: int):
        # TODO: Implement approve logic
        pass

    def deny_incident(self, incident_id: int):
        # TODO: Implement deny logic
        pass

    def incident_analysis(self, log_text: str):
        """
        Run threat analysis and return the result (State).
        Automatically records the results in the database with a thread_id.
        """
        thread_id = str(uuid.uuid4())

        initial_state: AgentState = {
            "messages": [HumanMessage(content=f"{LOG_ANALYSIS_REQUEST_PREFIX}{log_text}")],
            "analysis_result": None,  # type: ignore
            "context": {"source": "log_analytics_service"},
        }

        logger.info(f"[Starting Threat Analysis - Thread ID: {thread_id}]")

        # Use invoke to get the final state
        final_state = self.threat_agent.invoke(
            initial_state, config={"configurable": {"thread_id": thread_id}}
        )

        analysis_dict = None
        is_threat = False

        if final_state.get("analysis_result"):
            analysis = final_state["analysis_result"]
            analysis_dict = analysis.model_dump()
            is_threat = analysis.is_true_positive

            logger.info("[Threat Analysis Completed]")
            logger.info(f" - Verdict: {'True Positive' if is_threat else 'False Positive'}")
            logger.info(f" - Confidence Score: {analysis.confidence_score}")
            logger.info(f" - Attack Type: {analysis.attack_type}")
            logger.info(f" - Summary: {analysis.executive_summary}")
            
            logger.debug(
                json.dumps(
                    analysis_dict,
                    ensure_ascii=False,
                    indent=2,
                )
            )

        logger.info("Storing analysis results in the database...")

        with self.session_factory() as db:
            try:
                self.create_incident_from_analysis(
                    db=db,
                    title=f"Auto Log Analysis - {thread_id[:8]}",
                    raw_log=log_text,
                    analysis_data=analysis_dict,
                    is_threat=is_threat,
                    thread_id=thread_id,
                )
                logger.info(f"DB Storage Completed (Thread ID: {thread_id})")
            except Exception as e:
                logger.error(f"DB Storage Error: {e}")

        # Return final_state including thread_id for external use
        final_state["thread_id"] = thread_id

        return final_state
