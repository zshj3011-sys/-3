"""数据库连接 - 异步 SQLAlchemy 2.0

开发使用 SQLite (aiosqlite), 生产使用 PostgreSQL (asyncpg).
切换只需改 DATABASE_URL 环境变量,无需改代码。
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


class Base(DeclarativeBase):
    """所有 ORM Model 的基类"""
    pass


# 异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG and settings.APP_ENV == "development",
    pool_pre_ping=True,
    # SQLite 不支持 pool 配置
    **({"connect_args": {"check_same_thread": False}} if "sqlite" in settings.DATABASE_URL else {}),
)

# 会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖: 每请求 Session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """启动时初始化所有表 (开发/演示模式用; 生产用 alembic)"""
    # 导入所有 model 以注册到 Base.metadata
    from app.models import (  # noqa: F401
        user, patient, doctor, department, medical_record,
        prescription, appointment, ai_conversation, drg, lab_report, audit_log
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
