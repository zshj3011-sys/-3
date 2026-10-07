"""挂号/预约"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models._common import TimestampMixin


class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"))

    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    visit_type: Mapped[str] = mapped_column(String(20), default="outpatient")  # outpatient|follow_up|emergency
    is_first_visit: Mapped[Optional[bool]]
    chief_complaint: Mapped[Optional[str]] = mapped_column(String(255))

    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    # scheduled|checked_in|in_progress|completed|cancelled|no_show

    ai_summary: Mapped[Optional[str]] = mapped_column(Text, comment="AI 预问诊摘要")
    triage_level: Mapped[Optional[str]] = mapped_column(String(10))  # red|yellow|green
