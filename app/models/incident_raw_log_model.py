from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.incident_model import Incident


class IncidentRawLog(Base):
    __tablename__: str = "incident_raw_logs"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_idx: Mapped[int] = mapped_column(
        ForeignKey("incidents.idx", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_logs: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    incident: Mapped["Incident"] = relationship()
