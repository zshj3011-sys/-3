"""消息通知 API — 实现 PRD 患者端 M1 §2 必备模块"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.notification import Notification
from app.models.user import User
from app.schemas.common import StandardResponse, PageResponse, PageMeta, OrmBase

router = APIRouter()


class NotificationOut(OrmBase):
    id: int
    user_id: int
    category: str
    title: str
    content: str
    severity: str
    is_read: bool
    read_at: Optional[datetime]
    link: Optional[str]
    related_type: Optional[str]
    related_id: Optional[int]
    created_at: datetime


class NotificationCreate(BaseModel):
    user_id: int
    category: str = "system"
    title: str
    content: str
    severity: str = "info"
    link: Optional[str] = None
    related_type: Optional[str] = None
    related_id: Optional[int] = None


class UnreadCount(BaseModel):
    total: int
    by_category: dict


@router.get("/", response_model=PageResponse[NotificationOut],
            summary="我的消息列表")
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
    is_read: Optional[bool] = None,
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    stmt = select(Notification).where(Notification.user_id == current.id)
    if is_read is not None:
        stmt = stmt.where(Notification.is_read == is_read)
    if category:
        stmt = stmt.where(Notification.category == category)
    stmt = stmt.order_by(Notification.created_at.desc())

    total = (await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )).scalar() or 0

    rows = (await db.execute(stmt.offset((page - 1) * size).limit(size))).scalars().all()
    items = [NotificationOut.model_validate(r) for r in rows]
    pages = (total + size - 1) // size if size else 0
    return PageResponse[NotificationOut](
        data=items,
        meta=PageMeta(total=total, page=page, page_size=size, total_pages=pages),
    )


@router.get("/unread-count", response_model=StandardResponse[UnreadCount],
            summary="未读消息计数")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    total = (await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current.id,
            Notification.is_read == False,  # noqa
        )
    )).scalar() or 0

    rows = (await db.execute(
        select(Notification.category, func.count(Notification.id)).where(
            Notification.user_id == current.id,
            Notification.is_read == False,  # noqa
        ).group_by(Notification.category)
    )).all()
    by_category = {cat: cnt for cat, cnt in rows}

    return StandardResponse(data=UnreadCount(total=total, by_category=by_category))


@router.patch("/{notif_id}/read", response_model=StandardResponse[NotificationOut],
              summary="标记单条已读")
async def mark_read(
    notif_id: int,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    n = await db.get(Notification, notif_id)
    if not n or n.user_id != current.id:
        raise HTTPException(404, "消息不存在")
    if not n.is_read:
        n.is_read = True
        n.read_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(n)
    return StandardResponse(data=NotificationOut.model_validate(n))


@router.post("/mark-all-read", response_model=StandardResponse[dict],
             summary="标记全部已读")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    res = await db.execute(
        update(Notification).where(
            Notification.user_id == current.id,
            Notification.is_read == False,  # noqa
        ).values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    return StandardResponse(data={"updated": res.rowcount or 0})


@router.post("/", response_model=StandardResponse[NotificationOut],
             summary="发送消息 (管理端/系统调用)")
async def send_notification(
    body: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if current.role not in ("admin", "doctor"):
        raise HTTPException(403, "仅管理员/医生可发送消息")
    n = Notification(**body.model_dump())
    db.add(n)
    await db.flush()
    await db.refresh(n)
    return StandardResponse(data=NotificationOut.model_validate(n))
