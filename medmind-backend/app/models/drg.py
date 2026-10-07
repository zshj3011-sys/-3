"""DRG/DIP 控费病案"""
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Float, JSON, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models._common import TimestampMixin


class DRGCase(Base, TimestampMixin):
    __tablename__ = "drg_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)

    patient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patients.id"))
    medical_record_id: Mapped[Optional[int]] = mapped_column(ForeignKey("medical_records.id"))
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"), index=True)

    primary_diagnosis: Mapped[Optional[str]] = mapped_column(String(255))
    icd10: Mapped[Optional[str]] = mapped_column(String(20), index=True)

    # DRG 分组
    drg_code: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    drg_name: Mapped[Optional[str]] = mapped_column(String(255))

    # 费用
    payment_standard: Mapped[Optional[float]] = mapped_column(Float, comment="医保支付标准")
    actual_cost: Mapped[Optional[float]] = mapped_column(Float, comment="实际花费")
    predicted_cost: Mapped[Optional[float]] = mapped_column(Float, comment="AI 预测费用")
    profit_loss: Mapped[Optional[float]] = mapped_column(Float, comment="盈亏")

    # 状态
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    # in_progress | closed | warned | exceeded
    risk_level: Mapped[Optional[str]] = mapped_column(String(10))  # green|amber|red
    ai_suggestions: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # 住院信息
    admission_date: Mapped[Optional[str]] = mapped_column(String(20))
    discharge_date: Mapped[Optional[str]] = mapped_column(String(20))
    length_of_stay: Mapped[Optional[int]] = mapped_column(Integer)
    insurance_type: Mapped[Optional[str]] = mapped_column(String(20))  # 医保|自费|商保
