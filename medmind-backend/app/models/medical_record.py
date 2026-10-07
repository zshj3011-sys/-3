"""病历表 - 含 SOAP 格式 + ICD-10 编码 + AI 质控"""
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Text, JSON, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models._common import TimestampMixin


class MedicalRecord(Base, TimestampMixin):
    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="SET NULL"), index=True)
    appointment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("appointments.id"))

    # SOAP 四部分,各自独立字段方便检索
    subjective: Mapped[Optional[str]] = mapped_column(Text, comment="S 主观: 主诉/现病史")
    objective: Mapped[Optional[str]] = mapped_column(Text, comment="O 客观: 查体/检验/检查")
    assessment: Mapped[Optional[str]] = mapped_column(Text, comment="A 评估: 诊断/鉴别诊断")
    plan: Mapped[Optional[str]] = mapped_column(Text, comment="P 计划: 治疗方案")

    # 元数据
    chief_complaint: Mapped[Optional[str]] = mapped_column(String(255))  # 主诉摘要
    icd10_codes: Mapped[Optional[list]] = mapped_column(JSON, default=list)  # ["I20.0", "I10"]
    record_type: Mapped[str] = mapped_column(String(20), default="outpatient")  # outpatient|inpatient|emergency
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|submitted|signed
    ai_assisted: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_draft_raw: Mapped[Optional[str]] = mapped_column(Text, comment="AI 原始草稿(留痕)")

    # 质控
    quality_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    quality_issues: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    signed_at: Mapped[Optional[str]] = mapped_column(String(30))

    def __repr__(self) -> str:
        return f"<MedicalRecord #{self.id} patient={self.patient_id} status={self.status}>"
