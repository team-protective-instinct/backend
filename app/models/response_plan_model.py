from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.constants import ResponsePlanStatus

if TYPE_CHECKING:
    from app.models.incident_model import Incident
    from app.models.response_plan_action_model import ResponsePlanAction


class ResponsePlan(Base):
    __tablename__: str = "response_plans"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_idx: Mapped[int] = mapped_column(
        ForeignKey("incidents.idx", ondelete="CASCADE"), nullable=False, index=True
    )
    thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, default=ResponsePlanStatus.PENDING
    )
    denied_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    incident: Mapped["Incident"] = relationship()
    actions: Mapped[list["ResponsePlanAction"]] = relationship(
        back_populates="response_plan",
        cascade="all, delete-orphan",
        order_by="ResponsePlanAction.execution_order",
        lazy="selectin",
    )
