import json
import logging
import uuid
from typing import cast

from langchain_core.messages import HumanMessage

from app.agents.incident_analyzer.agent import ThreatAnalyzerAgent
from app.agents.incident_analyzer.prompt import LOG_ANALYSIS_REQUEST_PREFIX
from app.agents.incident_analyzer.state import AgentState
from app.agents.response_plan_agent.agent import ResponsePlanAgent
from app.agents.response_plan_agent.state import ResponsePlanState
from app.models import Incident, IncidentReport
from app.schemas import AnalysisReport, ResponsePlanDraft
from app.services.playbook_service import PlaybookService


logger = logging.getLogger(__name__)

MAX_INCIDENT_AGENT_INPUT_CHARS = 12000


class AiInvokerService:
    def __init__(
        self,
        threat_agent: ThreatAnalyzerAgent,
        response_plan_agent: ResponsePlanAgent,
        playbook_service: PlaybookService,
    ):
        self.threat_agent = threat_agent
        self.response_plan_agent = response_plan_agent
        self.playbook_service = playbook_service

    def generate_incident_reports(self, log_text: str) -> tuple[str, AnalysisReport]:
        thread_id = str(uuid.uuid4())
        bounded_log_text = self._truncate_for_llm(log_text)
        logger.info(
            "AI report started - thread_id=%s input_chars=%d",
            thread_id,
            len(bounded_log_text),
        )
        initial_state: AgentState = {
            "messages": [
                HumanMessage(content=f"{LOG_ANALYSIS_REQUEST_PREFIX}{bounded_log_text}")
            ],
            "context": {"source": "incident_agent_worker"},
        }

        logger.info("[Starting Threat Analysis - Thread ID: %s]", thread_id)
        final_state = cast(
            AgentState,
            self.threat_agent.invoke(
                initial_state, config={"configurable": {"thread_id": thread_id}}
            ),
        )

        analysis = final_state.get("analysis_result")
        if analysis is None:
            raise RuntimeError("Incident agent did not generate an analysis report")

        logger.info("[Threat Analysis Completed]")
        logger.info(
            " - Verdict: %s",
            "True Positive" if analysis.is_true_positive else "False Positive",
        )
        logger.info(" - Severity: %s", analysis.severity)
        logger.info(" - Confidence Score: %s", analysis.confidence_score)
        logger.info(" - Attack Type: %s", analysis.attack_type)
        logger.info(" - Primary Attacker IP: %s", analysis.attack_ip)
        logger.info(" - Summary: %s", analysis.analysis_summary)
        logger.info(
            "AI report completed - thread_id=%s verdict=%s severity=%s confidence=%.3f attack_type=%s",
            thread_id,
            "TP" if analysis.is_true_positive else "FP",
            analysis.severity,
            analysis.confidence_score,
            analysis.attack_type,
        )

        return thread_id, analysis

    def generate_incident_response_plan(
        self, incident: Incident, report: IncidentReport, raw_log: str
    ) -> tuple[str, ResponsePlanDraft]:
        context = self._build_agent_context(incident, report, raw_log)
        query = self._build_retrieval_query(context)
        logger.info(
            "Response plan started - incident_idx=%s attack_type=%s severity=%s raw_log_chars=%d query_chars=%d",
            incident.idx,
            report.attack_type,
            incident.severity,
            len(raw_log),
            len(query),
        )
        retrieved_chunks = self.playbook_service.retrieve_relevant_chunks(
            query=query,
            limit=5,
        )

        thread_id = f"response-plan:{incident.idx}:{uuid.uuid4()}"
        initial_state: ResponsePlanState = {
            "context": context,
            "retrieved_chunks": [
                self.playbook_service.retrieval_result_to_dict(chunk)
                for chunk in retrieved_chunks
            ],
        }
        final_state = cast(
            ResponsePlanState,
            self.response_plan_agent.invoke(
                initial_state,
                config={"configurable": {"thread_id": thread_id}},
            ),
        )
        draft = final_state.get("response_plan")
        if draft is None:
            raise RuntimeError("ResponsePlanAgent did not generate a response plan")
        logger.info(
            "Response plan completed - incident_idx=%s thread_id=%s summary_chars=%d plan_chars=%d",
            incident.idx,
            thread_id,
            len(draft.summary),
            len(draft.plan_text),
        )
        return thread_id, draft

    def _build_retrieval_query(self, context: dict[str, object]) -> str:
        parts = [
            str(context.get("attack_type") or ""),
            str(context.get("severity") or ""),
            str(context.get("analysis_summary") or ""),
            " ".join(cast(list[str], context.get("target_uris") or [])),
            " ".join(cast(list[str], context.get("suspicious_payloads") or [])),
            str(context.get("raw_log") or ""),
        ]
        return "\n".join(part for part in parts if part.strip())

    def _build_agent_context(
        self, incident: Incident, report: IncidentReport, raw_log: str
    ) -> dict[str, object]:
        analysis = (
            report.analysis_result if isinstance(report.analysis_result, dict) else {}
        )
        return {
            "incident_idx": incident.idx,
            "title": incident.title,
            "severity": incident.severity,
            "attack_type": report.attack_type,
            "confidence_score": report.confidence_score,
            "attacker_ip": report.attacker_ip,
            "analysis_summary": report.analysis_summary,
            "analysis_result": analysis,
            "target_uris": self._get_string_list(analysis, "target_uris"),
            "suspicious_payloads": self._get_string_list(
                analysis, "suspicious_payloads"
            ),
            "raw_log": raw_log[:6000],
            "created_at": incident.created_at.isoformat(),
        }

    def _get_string_list(self, data: dict[str, object], key: str) -> list[str]:
        value = data.get(key)
        if not isinstance(value, list):
            return []
        return [str(item) for item in value]

    def _truncate_for_llm(self, value: str) -> str:
        if len(value) <= MAX_INCIDENT_AGENT_INPUT_CHARS:
            return value
        omitted = len(value) - MAX_INCIDENT_AGENT_INPUT_CHARS
        return f"{value[:MAX_INCIDENT_AGENT_INPUT_CHARS]}\n...[truncated {omitted} chars before LLM analysis]"
