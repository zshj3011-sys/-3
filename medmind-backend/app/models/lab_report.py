"""检验报告 (化验单)"""
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models._common import TimestampMixin


class LabReport(Base, TimestampMixin):
    __tablename__ = "lab_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    doctor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("doctors.id"))

    report_type: Mapped[str] = mapped_column(String(30))  # 血常规|血脂|肝功|肾功|心肌酶|CT|MRI|X-ray
    report_date: Mapped[Optional[str]] = mapped_column(String(20))
    indicators: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    # [{"name":"LDL-C","value":4.2,"unit":"mmol/L","range":"<3.4","flag":"high"}, ...]

    abnormal_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    ai_interpretation: Mapped[Optional[str]] = mapped_column(Text)
    ai_suggestions: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    raw_image_url: Mapped[Optional[str]] = mapped_column(String(255))
