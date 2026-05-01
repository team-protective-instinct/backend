from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Boolean, JSON, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.constants import IncidentStatus


class Incident(Base):
    __tablename__: str = "incidents"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    thread_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=IncidentStatus.ANALYZING)
    evidence_logs: Mapped[str | None] = mapped_column(Text, nullable=True) # Text로 변경하여 큰 원본 로그 허용
    analysis_result: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_identified_threat: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    severity: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True) # critical, high, medium, low
    attack_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True) # SQL Injection 등
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True) # 0.0 ~ 1.0
    attacker_ip: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True) # 주요 공격자 IP
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    modified_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
