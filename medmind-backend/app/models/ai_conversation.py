"""AI 多轮对话 (预问诊/诊间助手等)"""
from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models._common import TimestampMixin


class AIConversation(Base, TimestampMixin):
    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    patient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patients.id"), index=True)

    scenario: Mapped[str] = mapped_column(String(30), index=True)
    # pre_triage | consultation | diagnosis | rx_audit | grant | paper_polish | health_qa

    agent_name: Mapped[str] = mapped_column(String(30), default="default")
    model: Mapped[Optional[str]] = mapped_column(String(60))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    soap_summary: Mapped[Optional[dict]] = mapped_column(JSON)  # S/O/A/P
    triage_level: Mapped[Optional[str]] = mapped_column(String(10))
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active|completed|aborted
    extras: Mapped[Optional[dict]] = mapped_column(JSON)

    messages: Mapped[List["AIMessage"]] = relationship(
        "AIMessage", back_populates="conversation",
        cascade="all, delete-orphan", order_by="AIMessage.id"
    )


class AIMessage(Base):
    __tablename__ = "ai_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("ai_conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))  # user|assistant|system|tool
    content: Mapped[str] = mapped_column(Text)
    quick_replies: Mapped[Optional[list]] = mapped_column(JSON)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    citations: Mapped[Optional[list]] = mapped_column(JSON)

    conversation: Mapped["AIConversation"] = relationship("AIConversation", back_populates="messages")
