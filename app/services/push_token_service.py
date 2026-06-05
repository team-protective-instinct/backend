from typing import Callable

from sqlalchemy.orm import Session

from app.models import PushToken
from app.schemas.push_token_schema import PushTokenRegisterRequest


ACTIVE_EXPO_TOKEN_LIMIT = 50


class PushTokenService:
    def __init__(self, session_factory: Callable[..., Session]):
        self.session_factory: Callable[..., Session] = session_factory

    def register(self, request: PushTokenRegisterRequest) -> PushToken:
        token_value = request.token.strip()
        if not token_value:
            raise ValueError("Push token must not be empty")

        with self.session_factory() as db:
            push_token = (
                db.query(PushToken).filter(PushToken.token == token_value).first()
            )
            if push_token is None:
                push_token = PushToken(
                    token=token_value,
                    provider=request.provider,
                    platform=request.platform,
                    device_name=request.device_name,
                    is_active=True,
                )
                db.add(push_token)
            else:
                push_token.provider = request.provider
                push_token.platform = request.platform
                push_token.device_name = request.device_name
                push_token.is_active = True

            db.commit()
            db.refresh(push_token)
            return push_token

    def list_tokens(self, active_only: bool = True) -> list[PushToken]:
        with self.session_factory() as db:
            query = db.query(PushToken)
            if active_only:
                query = query.filter(PushToken.is_active.is_(True))
            return query.order_by(PushToken.modified_at.desc()).all()

    def list_active_expo_tokens(
        self,
        limit: int = ACTIVE_EXPO_TOKEN_LIMIT,
    ) -> list[PushToken]:
        with self.session_factory() as db:
            return (
                db.query(PushToken)
                .filter(
                    PushToken.is_active.is_(True),
                    PushToken.provider == "expo",
                )
                .order_by(PushToken.modified_at.desc())
                .limit(limit)
                .all()
            )

    def deactivate(self, push_token_idx: int) -> PushToken:
        with self.session_factory() as db:
            push_token = (
                db.query(PushToken).filter(PushToken.idx == push_token_idx).first()
            )
            if push_token is None:
                raise ValueError("Push token not found")

            push_token.is_active = False
            db.commit()
            db.refresh(push_token)
            return push_token

    def deactivate_by_token(self, token: str) -> None:
        token_value = token.strip()
        if not token_value:
            return

        with self.session_factory() as db:
            push_token = (
                db.query(PushToken).filter(PushToken.token == token_value).first()
            )
            if push_token is None:
                return

            push_token.is_active = False
            db.commit()
