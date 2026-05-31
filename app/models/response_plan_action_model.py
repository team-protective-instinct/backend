from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.constants import ResponsePlanActionStatus

if TYPE_CHECKING:
    from app.models.response_plan_model import ResponsePlan


class ResponsePlanAction(Base):
    __tablename__: str = "response_plan_actions"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    response_plan_idx: Mapped[int] = mapped_column(
        ForeignKey("response_plans.idx", ondelete="CASCADE"), nullable=False, index=True
    )
    execution_order: Mapped[int] = mapped_column(Integer, nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    arguments: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
        default=ResponsePlanActionStatus.PENDING.value,
    )
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    response_plan: Mapped["ResponsePlan"] = relationship(back_populates="actions")
