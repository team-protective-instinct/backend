from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.constants import IncidentAnalysisStatus, IncidentStatus


class Incident(Base):
    __tablename__: str = "incidents"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=IncidentStatus.ANALYZING)
    is_identified_threat: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    analysis_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        default=IncidentAnalysisStatus.PENDING.value,
    )
    analysis_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    analysis_last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    response_plan_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    response_plan_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    response_plan_last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    severity: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True) # critical, high, medium, low
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    modified_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
