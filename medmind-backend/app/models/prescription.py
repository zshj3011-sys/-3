"""处方 + 处方项"""
from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, Text, JSON, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models._common import TimestampMixin


class Prescription(Base, TimestampMixin):
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rx_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="SET NULL"), index=True)
    medical_record_id: Mapped[Optional[int]] = mapped_column(ForeignKey("medical_records.id"))

    diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    instructions: Mapped[Optional[str]] = mapped_column(Text, comment="医嘱/用药指导")
    total_amount: Mapped[Optional[float]] = mapped_column(Float)
    insurance_amount: Mapped[Optional[float]] = mapped_column(Float)
    self_pay_amount: Mapped[Optional[float]] = mapped_column(Float)

    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|reviewed|dispensed|cancelled
    ai_assisted: Mapped[bool] = mapped_column(Boolean, default=False)

    # AI 审核结果
    audit_score: Mapped[Optional[float]] = mapped_column(Float)
    audit_warnings: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    audit_passed: Mapped[Optional[bool]] = mapped_column(Boolean)

    items: Mapped[List["PrescriptionItem"]] = relationship(
        "PrescriptionItem", back_populates="prescription",
        cascade="all, delete-orphan"
    )


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prescription_id: Mapped[int] = mapped_column(ForeignKey("prescriptions.id", ondelete="CASCADE"), index=True)

    drug_name: Mapped[str] = mapped_column(String(120), nullable=False)
    drug_code: Mapped[Optional[str]] = mapped_column(String(40))  # 国药准字
    spec: Mapped[Optional[str]] = mapped_column(String(60))  # 规格 e.g. 100mg×30
    dose: Mapped[Optional[str]] = mapped_column(String(60))  # 单次剂量 e.g. 100mg
    frequency: Mapped[Optional[str]] = mapped_column(String(30))  # qd|bid|tid|qid|prn
    route: Mapped[Optional[str]] = mapped_column(String(20))  # 口服|静滴|肌注|外用
    duration_days: Mapped[Optional[int]] = mapped_column(Integer)
    quantity: Mapped[Optional[float]] = mapped_column(Float)
    unit: Mapped[Optional[str]] = mapped_column(String(20))  # 片/支/瓶
    unit_price: Mapped[Optional[float]] = mapped_column(Float)
    note: Mapped[Optional[str]] = mapped_column(Text)
    ai_tag: Mapped[Optional[str]] = mapped_column(String(40))  # AI推荐|剂量调整|长期用药

    prescription: Mapped["Prescription"] = relationship("Prescription", back_populates="items")
