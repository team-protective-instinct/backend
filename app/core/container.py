from dependency_injector import containers, providers

from .config import Settings
from .database import Database
from app.services.crypt_service import CryptService
from app.services.jwt_service import JWTService
from app.services.user_service import UserService
from app.services.incident_service import IncidentService
from app.agents.incident_analyzer.agent import ThreatAnalyzerAgent


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

    user_service = providers.Factory(
        UserService,
        session_factory=db.provided.session,
        crypt_service=crypt_service,
    )

    incident_service = providers.Factory(
        IncidentService,
        session_factory=db.provided.session,
        threat_agent=threat_agent,
    )
