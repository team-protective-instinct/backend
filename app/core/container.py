from dependency_injector import containers, providers

from .config import Settings
from .database import Database
from app.services.crypt_service import CryptService
from app.services.jwt_service import JWTService
from app.services.user_service import UserService
from app.services.incident_service import IncidentService
from app.agents.incident_analyzer.agent import ThreatAnalyzerAgent
from app.agents.response_plan_agent.agent import ResponsePlanAgent
from app.services.playbook_service import PlaybookService
from app.services.response_plan_service import ResponsePlanService


class Container(containers.DeclarativeContainer):
    config = providers.Singleton(Settings)

    db = providers.Singleton(
        Database,
        settings=config,
    )

    crypt_service = providers.Factory(
        CryptService,
    )

    jwt_service = providers.Factory(
        JWTService,
        settings=config,
    )

    threat_agent = providers.Singleton(
        ThreatAnalyzerAgent,
        db_pool=db.provided.pool,
    )

    response_plan_agent = providers.Singleton(
        ResponsePlanAgent,
        db_pool=db.provided.pool,
    )

    playbook_service = providers.Factory(
        PlaybookService,
        session_factory=db.provided.session,
    )

    response_plan_service = providers.Factory(
        ResponsePlanService,
        session_factory=db.provided.session,
        response_plan_agent=response_plan_agent,
        playbook_service=playbook_service,
    )

    user_service = providers.Factory(
        UserService,
        session_factory=db.provided.session,
        crypt_service=crypt_service,
    )

    incident_service = providers.Factory(
        IncidentService,
        session_factory=db.provided.session,
        threat_agent=threat_agent,
        response_plan_service=response_plan_service,
    )
