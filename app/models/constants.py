from enum import Enum


class IncidentStatus(str, Enum):
    ANALYZING = "analyzing"
    PENDING_REVIEW = "pending_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
