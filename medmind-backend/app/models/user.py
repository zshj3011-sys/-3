"""用户表 - 对应 PRD M6 §1.2.1"""
from typing import Optional
from sqlalchemy import String, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base
from app.models._common import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    full_name: Mapped[Optional[str]] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="patient",
        comment="patient|doctor|pharmacist|admin|researcher"
    )
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<User {self.username} role={self.role}>"
