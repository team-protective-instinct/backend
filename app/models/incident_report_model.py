from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.incident_model import Incident


class IncidentReport(Base):
    __tablename__: str = "incident_reports"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_idx: Mapped[int] = mapped_column(
        ForeignKey("incidents.idx", ondelete="CASCADE"), nullable=False, index=True
    )
    thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    attack_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    attacker_ip: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    analysis_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_result: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    incident: Mapped["Incident"] = relationship()
