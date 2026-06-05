from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models import PushToken


PushTokenProvider = Literal["expo"]
PushTokenPlatform = Literal["ios", "android", "web", "unknown"]


class PushTokenRegisterRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)
    provider: PushTokenProvider = "expo"
    platform: PushTokenPlatform = "unknown"
    device_name: str | None = Field(default=None, max_length=255)


class PushNotificationTestRequest(BaseModel):
    title: str = Field(default="Test notification", min_length=1, max_length=100)
    body: str = Field(
        default="Expo push notification test from backend.",
        min_length=1,
        max_length=500,
    )
    incident_idx: int | None = Field(default=None, ge=1)


class PushNotificationTestResponse(BaseModel):
    sent_count: int
    skipped_reason: str | None = None


class PushTokenResponse(BaseModel):
    idx: int
    token: str
    provider: str
    platform: str
    device_name: str | None
    is_active: bool
    created_at: datetime
    modified_at: datetime

    @classmethod
    def from_push_token(cls, push_token: PushToken) -> "PushTokenResponse":
        return cls(
            idx=push_token.idx,
            token=push_token.token,
            provider=push_token.provider,
            platform=push_token.platform,
            device_name=push_token.device_name,
            is_active=push_token.is_active,
            created_at=push_token.created_at,
            modified_at=push_token.modified_at,
        )
