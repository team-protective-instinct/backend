import asyncio
import json
import logging
from urllib import error, request

from app.core.config import Settings
from app.schemas import ExpoPushMessage
from app.services.push_token_service import PushTokenService


logger = logging.getLogger(__name__)

DEVICE_NOT_REGISTERED = "DeviceNotRegistered"


class NotificationService:
    def __init__(
        self,
        settings: Settings,
        push_token_service: PushTokenService,
    ):
        self.settings = settings
        self.push_token_service = push_token_service

    async def send_notification(self, messages: list[ExpoPushMessage]) -> int:
        if not self.settings.EXPO_PUSH_ENABLED:
            logger.info("Expo push disabled; skipping notification")
            return 0

        if not messages:
            logger.info("No Expo push messages; skipping notification")
            return 0

        await asyncio.to_thread(self._send_messages, messages)
        return len(messages)

    def _send_messages(self, messages: list[ExpoPushMessage]) -> None:
        payload = [message.to_payload() for message in messages]
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.settings.EXPO_PUSH_ACCESS_TOKEN:
            headers["Authorization"] = f"Bearer {self.settings.EXPO_PUSH_ACCESS_TOKEN}"

        expo_request = request.Request(
            self.settings.EXPO_PUSH_URL,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with request.urlopen(
                expo_request,
                timeout=self.settings.EXPO_PUSH_REQUEST_TIMEOUT_SECONDS,
            ) as response:
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            logger.warning(
                "Expo push request failed - status=%s body=%s",
                exc.code,
                exc.read().decode("utf-8", errors="replace"),
            )
            return
        except (OSError, TimeoutError) as exc:
            logger.warning("Expo push request failed: %s", exc)
            return

        self._handle_expo_response(messages, response_body)

    def _handle_expo_response(
        self,
        messages: list[ExpoPushMessage],
        response_body: str,
    ) -> None:
        try:
            parsed = json.loads(response_body)
        except json.JSONDecodeError:
            logger.warning("Expo push response was not valid JSON")
            return

        tickets = parsed.get("data") if isinstance(parsed, dict) else None
        if not isinstance(tickets, list):
            logger.warning("Expo push response missing data tickets")
            return

        for message, ticket in zip(messages, tickets, strict=False):
            if not isinstance(ticket, dict):
                continue

            if ticket.get("status") == "ok":
                continue

            details = ticket.get("details")
            error_name = details.get("error") if isinstance(details, dict) else None
            logger.warning(
                "Expo push ticket failed - error=%s message=%s",
                error_name or "unknown",
                ticket.get("message") or "",
            )
            if error_name == DEVICE_NOT_REGISTERED:
                self.push_token_service.deactivate_by_token(message.to)
