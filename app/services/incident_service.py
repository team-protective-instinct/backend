import json
import uuid
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session
from app.agents import AgentState, threat_agent_graph
from app.agents.incident_analyzer.prompt import LOG_ANALYSIS_REQUEST_PREFIX
from app.models import Incident
from app.core.database import SessionLocal


def create_incident(db: Session, title: str, description: str):
    incident = Incident(title=title, description=description)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def create_incident_from_analysis(
    db: Session,
    title: str,
    raw_log: str,
    verdict_data: dict,
    report_data: dict,
    is_threat: bool,
    thread_id: str,
) -> Incident:
    incident = Incident(
        thread_id=thread_id,
        title=title,
        status="completed",
        evidence_logs=raw_log,
        verdict_json=verdict_data,
        report_json=report_data,
        is_identified_threat=is_threat,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def get_pending_incidents(db: Session):
    return db.query(Incident).filter(Incident.status == "pending").all()


def get_incident_by_idx(db: Session, incident_idx: int):
    return db.query(Incident).filter(Incident.idx == incident_idx).first()


def approve_incident(db: Session, incident_id: int):
    pass


def deny_incident(db: Session, incident_id: int):
    pass


def incident_analysis(log_text: str):
    """
    Run threat analysis and return the result (State).
    Automatically records the results in the database with a thread_id.
    """
    thread_id = str(uuid.uuid4())

    initial_state: AgentState = {
        "messages": [HumanMessage(content=f"{LOG_ANALYSIS_REQUEST_PREFIX}{log_text}")],
        "final_analysis": None,
        "incident_report": None,
    }

    print(f"[Starting Threat Analysis - Thread ID: {thread_id}]")

    # Use invoke to get the final state
    final_state = threat_agent_graph.invoke(
        initial_state, config={"configurable": {"thread_id": thread_id}}
    )

    verdict_dict = None
    report_dict = None
    is_threat = False

    if final_state.get("final_analysis"):
        analysis = final_state["final_analysis"]
        verdict_dict = analysis.model_dump()
        is_threat = analysis.is_true_positive

        print("[Step 1: Final Verdict Completed]")
        print(f" - Verdict: {'True Positive' if is_threat else 'False Positive'}")
        print(f" - Confidence Score: {analysis.confidence_score}")
        print(f" - Summary: {analysis.executive_summary}")

    if final_state.get("incident_report"):
        report = final_state["incident_report"]
        report_dict = report.model_dump()
        print("[Step 2: Incident Report Generated]")
        print(
            json.dumps(
                report_dict,
                ensure_ascii=False,
                indent=2,
            )
        )

    print("Storing analysis results in the database...")

    db = SessionLocal()
    try:
        create_incident_from_analysis(
            db=db,
            title=f"Auto Log Analysis - {thread_id[:8]}",
            raw_log=log_text,
            verdict_data=verdict_dict,
            report_data=report_dict,
            is_threat=is_threat,
            thread_id=thread_id,
        )
        print(f"DB Storage Completed (Thread ID: {thread_id})")
    except Exception as e:
        print(f"DB Storage Error: {e}")
    finally:
        db.close()

    # Return final_state including thread_id for external use
    final_state["thread_id"] = thread_id

    return final_state
