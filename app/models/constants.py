from enum import Enum


class IncidentStatus(str, Enum):
    ANALYZING = "analyzing"
    PENDING_REVIEW = "pending_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ResponsePlanStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTING = "executing"
    EXECUTED = "executed"
