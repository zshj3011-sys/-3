"""消息通知 — PRD 患者端核心模块 (M1 §2 功能架构)"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models._common import TimestampMixin


class Notification(Base, TimestampMixin):
    """消息通知 — 患者/医生收到的系统消息。"""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(30), index=True,
        comment="appointment|medication|report|followup|system|ai_alert")
    title: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(10), default="info",
        comment="info|warn|critical")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    # 跳转目标 (前端用)
    link: Mapped[Optional[str]] = mapped_column(String(255))
    # 关联业务实体, 可选
    related_type: Mapped[Optional[str]] = mapped_column(String(30))  # appointment|record|prescription
    related_id: Mapped[Optional[int]]
