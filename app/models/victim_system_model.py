from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class VictimSystem(Base):
    __tablename__ = "victim_systems"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    mcp_status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
