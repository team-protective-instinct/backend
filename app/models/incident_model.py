from sqlalchemy import DateTime, Integer, String, Boolean, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    thread_id = mapped_column(String(255), nullable=False)
    title = mapped_column(String(255), nullable=False)
    status = mapped_column(String(50), nullable=False)
    evidence_logs = mapped_column(Text, nullable=True) # Text로 변경하여 큰 원본 로그 허용
    analysis_result = mapped_column(JSON, nullable=True)
    is_identified_threat = mapped_column(Boolean, nullable=True)
    
    created_at = mapped_column(DateTime, default=func.now(), nullable=False)
    modified_at = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
