from enum import Enum


class IncidentStatus(str, Enum):
    ANALYZING = "analyzing"
    PENDING_REVIEW = "pending_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class IncidentAnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IncidentResponsePlanStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IncidentRawLogSourceType(str, Enum):
    WEBHOOK = "webhook"
    ELASTICSEARCH_MCP = "elasticsearch_mcp"


class ResponsePlanStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"


class ResponsePlanActionStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"
    SKIPPED = "skipped"
