"""患者表 - 对应 PRD M6 §1.2.2"""
from datetime import date
from typing import Optional
from sqlalchemy import String, Integer, Date, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models._common import TimestampMixin


class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    real_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="生产环境应加密")
    id_card: Mapped[Optional[str]] = mapped_column(String(20), index=True, comment="生产环境应加密")
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    gender: Mapped[Optional[str]] = mapped_column(String(10))  # 男|女|其他
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(String(200))
    # 数组在 SQLite 用 JSON, PG 可改 ARRAY
    allergy_history: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    past_history: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    emergency_contact: Mapped[Optional[dict]] = mapped_column(JSON)
    health_summary: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<Patient {self.real_name}>"

    def age(self) -> Optional[int]:
        if not self.birth_date:
            return None
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
