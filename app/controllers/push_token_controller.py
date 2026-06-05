from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.container import Container
from app.schemas import (
    ExpoPushMessage,
    PushNotificationTestRequest,
    PushNotificationTestResponse,
    PushTokenRegisterRequest,
    PushTokenResponse,
)
from app.services.notification_service import NotificationService
from app.services.push_token_service import PushTokenService


router = APIRouter(prefix="/push-tokens", tags=["push-tokens"])


@router.post("/test", response_model=PushNotificationTestResponse)
@inject
async def send_test_push_notification(
    request: PushNotificationTestRequest,
    push_notification_service: NotificationService = Depends(
        Provide[Container.notification_service]
    ),
    push_token_service: PushTokenService = Depends(
        Provide[Container.push_token_service]
    ),
):
    if not push_notification_service.settings.EXPO_PUSH_ENABLED:
        return PushNotificationTestResponse(
            sent_count=0,
            skipped_reason="Expo push is disabled",
        )

    push_tokens = push_token_service.list_active_expo_tokens()
    if not push_tokens:
        return PushNotificationTestResponse(
            sent_count=0,
            skipped_reason="No active Expo push tokens",
        )

    data = {"type": "test_notification"}
    if request.incident_idx is not None:
        incident_idx = str(request.incident_idx)
        data["incident_idx"] = incident_idx
        data["url"] = f"/incidents/{incident_idx}"

    messages = [
        ExpoPushMessage(
            to=push_token.token,
            title=request.title,
            body=request.body,
            data=data,
        )
        for push_token in push_tokens
    ]
    sent_count = await push_notification_service.send_notification(messages)
    return PushNotificationTestResponse(sent_count=sent_count)


@router.post("", response_model=PushTokenResponse, status_code=status.HTTP_201_CREATED)
@inject
def register_push_token(
    request: PushTokenRegisterRequest,
    push_token_service: PushTokenService = Depends(
        Provide[Container.push_token_service]
    ),
):
    try:
        push_token = push_token_service.register(request)
    except ValueError as exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exception),
        ) from exception

    return PushTokenResponse.from_push_token(push_token)


@router.get("", response_model=list[PushTokenResponse])
@inject
def get_push_tokens(
    active_only: bool = Query(default=True),
    push_token_service: PushTokenService = Depends(
        Provide[Container.push_token_service]
    ),
):
    push_tokens = push_token_service.list_tokens(active_only=active_only)
    return [PushTokenResponse.from_push_token(push_token) for push_token in push_tokens]


@router.delete("/{push_token_idx}", response_model=PushTokenResponse)
@inject
def deactivate_push_token(
    push_token_idx: int,
    push_token_service: PushTokenService = Depends(
        Provide[Container.push_token_service]
    ),
):
    try:
        push_token = push_token_service.deactivate(push_token_idx)
    except ValueError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exception),
        ) from exception

    return PushTokenResponse.from_push_token(push_token)
