"""医疗安全事件上报 — PRD §07 用户故事 #139 (Must · V1.0)

支持医院内的医疗安全事件全流程: 上报 → 调查 → 解决 → 归档.
为 v3.6.2 补齐项 (此前 v3.6 任务清单声称完成但实际未实现).
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models._common import TimestampMixin


class SafetyEvent(Base, TimestampMixin):
    """医疗安全事件 — 不良事件 / 用药差错 / 跌倒等。"""
    __tablename__ = "safety_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 事件分类 (国卫医疗质量安全相关分类)
    event_type: Mapped[str] = mapped_column(String(40), index=True,
        comment="medication_error|fall|surgical|infection|device_failure|misdiagnosis|other")
    severity: Mapped[str] = mapped_column(String(10), index=True,
        comment="i|ii|iii|iv (i 警告事件最重 → iv 隐患事件最轻)")
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    location: Mapped[Optional[str]] = mapped_column(String(120),
        comment="发生地点: 病房号/科室/手术室")
    occurred_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    # 上报人 (用户)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)

    # 关联对象 (可选)
    related_patient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patients.id", ondelete="SET NULL"))
    related_record_id: Mapped[Optional[int]] = mapped_column(ForeignKey("medical_records.id", ondelete="SET NULL"))

    # 流程状态
    status: Mapped[str] = mapped_column(String(20), default="reported", index=True,
        comment="reported|investigating|resolved|closed")
    handler_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"),
        comment="处理人 (通常为管理员或质控员)")

    # 调查与整改
    root_cause: Mapped[Optional[str]] = mapped_column(Text, comment="根因分析")
    corrective_action: Mapped[Optional[str]] = mapped_column(Text, comment="整改措施")
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
