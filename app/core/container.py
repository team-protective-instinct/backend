from dependency_injector import containers, providers

from .config import Settings
from .database import Database
from app.services.incident_service import IncidentService
from app.agents.incident_agent.agent import IncidentAgent
from app.agents.response_plan_agent.agent import ResponsePlanAgent
from app.services.playbook_service import PlaybookService
from app.services.response_plan_service import ResponsePlanService
from app.services.response_plan_action_service import ResponsePlanActionService
from app.services.response_plan_action_executor import ResponsePlanActionExecutor
from app.services.ai_invoker_service import AiInvokerService
from app.services.incident_raw_log_service import IncidentRawLogService
from app.services.incident_report_service import IncidentReportService


class Container(containers.DeclarativeContainer):
    config = providers.Singleton(Settings)

    db = providers.Singleton(
        Database,
        settings=config,
    )

    threat_agent = providers.Singleton(
        IncidentAgent,
        settings=config,
    )

    response_plan_agent = providers.Singleton(
        ResponsePlanAgent,
        settings=config,
    )

    playbook_service = providers.Factory(
        PlaybookService,
        session_factory=db.provided.session,
    )

    response_plan_service = providers.Factory(
        ResponsePlanService,
        session_factory=db.provided.session,
    )

    response_plan_action_service = providers.Factory(
        ResponsePlanActionService,
        session_factory=db.provided.session,
    )

    response_plan_action_executor = providers.Factory(
        ResponsePlanActionExecutor,
        action_service=response_plan_action_service,
        response_plan_service=response_plan_service,
        settings=config,
    )

    incident_raw_log_service = providers.Factory(
        IncidentRawLogService,
        session_factory=db.provided.session,
    )

    incident_report_service = providers.Factory(
        IncidentReportService,
        session_factory=db.provided.session,
    )

    ai_invoker_service = providers.Factory(
        AiInvokerService,
        threat_agent=threat_agent,
        response_plan_agent=response_plan_agent,
        playbook_service=playbook_service,
        raw_log_service=incident_raw_log_service,
    )

    incident_service = providers.Factory(
        IncidentService,
        session_factory=db.provided.session,
        raw_log_service=incident_raw_log_service,
        report_service=incident_report_service,
    )
