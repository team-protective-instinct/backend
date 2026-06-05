from dataclasses import dataclass


@dataclass(frozen=True)
class ExpoPushMessage:
    to: str
    title: str
    body: str
    data: dict[str, str]

    def to_payload(self) -> dict[str, object]:
        return {
            "to": self.to,
            "title": self.title,
            "body": self.body,
            "sound": "default",
            "channelId": "default",
            "data": self.data,
        }
