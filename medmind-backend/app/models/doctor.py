"""医生表"""
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models._common import TimestampMixin


class Doctor(Base, TimestampMixin):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    doctor_name: Mapped[str] = mapped_column(String(50), nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"), index=True)
    title: Mapped[Optional[str]] = mapped_column(String(30))  # 主任医师/副主任医师/主治医师/住院医师
    license_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    specialties: Mapped[Optional[str]] = mapped_column(Text)  # 擅长方向
    introduction: Mapped[Optional[str]] = mapped_column(Text)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255))
    rating: Mapped[Optional[float]] = mapped_column(Float, default=5.0)
    years_of_practice: Mapped[Optional[int]] = mapped_column(Integer)

    def __repr__(self) -> str:
        return f"<Doctor {self.doctor_name} {self.title}>"
