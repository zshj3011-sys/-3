"""审计日志 - 等保三级要求"""
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models._common import TimestampMixin


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    username: Mapped[Optional[str]] = mapped_column(String(50))

    action: Mapped[str] = mapped_column(String(50), index=True)
    # login|logout|access_patient|create_record|sign_record|prescribe|export|delete
    resource_type: Mapped[Optional[str]] = mapped_column(String(30))
    resource_id: Mapped[Optional[str]] = mapped_column(String(50))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    detail: Mapped[Optional[dict]] = mapped_column(JSON)
    result: Mapped[Optional[str]] = mapped_column(String(20))  # success|failure
    error_message: Mapped[Optional[str]] = mapped_column(Text)
