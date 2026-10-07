"""科研数据集 — PRD §07 用户故事 #165 (Must · V1.0)

研究者上传 Excel/CSV/SPSS 数据后, 后端做元数据存储 + 列类型嗅探,
为后续 `/research/statistics/recommend` 提供数据上下文.

v3.6.2 补齐.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, JSON, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models._common import TimestampMixin


class ResearchDataset(Base, TimestampMixin):
    """研究者上传的科研数据集。"""
    __tablename__ = "research_datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(200))
    original_filename: Mapped[str] = mapped_column(String(255))
    file_format: Mapped[str] = mapped_column(String(20), comment="csv|xlsx|sav")
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)

    # 嗅探结果
    rows: Mapped[int] = mapped_column(Integer, default=0)
    columns: Mapped[int] = mapped_column(Integer, default=0)
    schema_json: Mapped[Optional[str]] = mapped_column(JSON,
        comment="列元数据 list[{name, dtype, null_count, sample}]")
    preview_json: Mapped[Optional[str]] = mapped_column(JSON,
        comment="前 N 行预览数据")

    # 内容存储 (mock/demo: 直接放 JSON; 生产: 替换为 OSS 对象存储 key)
    content_key: Mapped[Optional[str]] = mapped_column(String(255),
        comment="预留: 生产环境的对象存储 key. 演示模式下为 NULL, 数据在 preview_json")
    notes: Mapped[Optional[str]] = mapped_column(Text, comment="用户备注")
