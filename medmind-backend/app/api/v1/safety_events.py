"""医疗安全事件上报 API — PRD §07 用户故事 #139 (Must · V1.0)

v3.6.2 新增. 提供完整的事件上报-调查-整改-归档闭环.
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.safety_event import SafetyEvent
from app.models.user import User
from app.schemas.common import StandardResponse, PageResponse, PageMeta, OrmBase

router = APIRouter()


# ============== Schema ==============
class SafetyEventCreate(BaseModel):
    event_type: str = Field(...,
        description="medication_error|fall|surgical|infection|device_failure|misdiagnosis|other")
    severity: str = Field(..., description="i|ii|iii|iv")
    title: str = Field(..., min_length=2, max_length=200)
    description: str
    location: Optional[str] = None
    occurred_at: datetime
    related_patient_id: Optional[int] = None
    related_record_id: Optional[int] = None


class SafetyEventOut(OrmBase):
    id: int
    event_type: str
    severity: str
    title: str
    description: str
    location: Optional[str]
    occurred_at: datetime
    reporter_id: int
    reporter_name: Optional[str] = None
    related_patient_id: Optional[int]
    related_record_id: Optional[int]
    status: str
    handler_id: Optional[int]
    handler_name: Optional[str] = None
    root_cause: Optional[str]
    corrective_action: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime


class SafetyEventStatusUpdate(BaseModel):
    status: str = Field(..., description="reported|investigating|resolved|closed")
    handler_id: Optional[int] = None
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None


class SafetyEventStats(BaseModel):
    total: int
    by_status: dict
    by_severity: dict
    by_type: dict
    last_30d: int


# ============== Helpers ==============
async def _serialize(db: AsyncSession, ev: SafetyEvent) -> SafetyEventOut:
    """补全展示用名字字段"""
    reporter = await db.get(User, ev.reporter_id) if ev.reporter_id else None
    handler = await db.get(User, ev.handler_id) if ev.handler_id else None
    return SafetyEventOut(
        id=ev.id, event_type=ev.event_type, severity=ev.severity, title=ev.title,
        description=ev.description, location=ev.location, occurred_at=ev.occurred_at,
        reporter_id=ev.reporter_id, reporter_name=reporter.full_name if reporter else None,
        related_patient_id=ev.related_patient_id, related_record_id=ev.related_record_id,
        status=ev.status, handler_id=ev.handler_id,
        handler_name=handler.full_name if handler else None,
        root_cause=ev.root_cause, corrective_action=ev.corrective_action,
        resolved_at=ev.resolved_at, created_at=ev.created_at,
    )


# ============== 端点 ==============
@router.post("/", response_model=StandardResponse[SafetyEventOut], summary="上报医疗安全事件")
async def report_event(
    body: SafetyEventCreate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """PRD §07 用户故事 #139: 任意角色都可上报, 默认状态 reported."""
    if body.event_type not in {
        "medication_error", "fall", "surgical",
        "infection", "device_failure", "misdiagnosis", "other"
    }:
        raise HTTPException(400, "event_type 取值不合法")
    if body.severity not in {"i", "ii", "iii", "iv"}:
        raise HTTPException(400, "severity 必须是 i/ii/iii/iv")
    ev = SafetyEvent(
        event_type=body.event_type, severity=body.severity,
        title=body.title, description=body.description,
        location=body.location, occurred_at=body.occurred_at,
        reporter_id=current.id,
        related_patient_id=body.related_patient_id,
        related_record_id=body.related_record_id,
        status="reported",
    )
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    out = await _serialize(db, ev)
    return StandardResponse(data=out)


@router.get("/", response_model=PageResponse[SafetyEventOut], summary="安全事件列表")
async def list_events(
    status: Optional[str] = Query(None, description="reported|investigating|resolved|closed"),
    severity: Optional[str] = Query(None, description="i|ii|iii|iv"),
    event_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """按多条件分页查询. 管理员看全部, 其他角色只看自己上报的."""
    stmt = select(SafetyEvent)
    conds = []
    if status:
        conds.append(SafetyEvent.status == status)
    if severity:
        conds.append(SafetyEvent.severity == severity)
    if event_type:
        conds.append(SafetyEvent.event_type == event_type)
    # 权限: 非管理员只看自己的
    if current.role != "admin":
        conds.append(SafetyEvent.reporter_id == current.id)
    if conds:
        stmt = stmt.where(and_(*conds))
    stmt = stmt.order_by(desc(SafetyEvent.occurred_at))

    # 总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # 分页
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(stmt)).scalars().all()
    data = [await _serialize(db, ev) for ev in rows]
    meta = PageMeta(page=page, page_size=page_size, total=total,
                    total_pages=(total + page_size - 1) // page_size if total else 0)
    return PageResponse(data=data, meta=meta)


@router.get("/stats", response_model=StandardResponse[SafetyEventStats], summary="安全事件统计")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """质控看板用. 按状态/严重程度/类型聚合."""
    total = (await db.execute(select(func.count(SafetyEvent.id)))).scalar() or 0

    # by_status
    rows = (await db.execute(
        select(SafetyEvent.status, func.count(SafetyEvent.id)).group_by(SafetyEvent.status)
    )).all()
    by_status = {r[0]: r[1] for r in rows}

    # by_severity
    rows = (await db.execute(
        select(SafetyEvent.severity, func.count(SafetyEvent.id)).group_by(SafetyEvent.severity)
    )).all()
    by_severity = {r[0]: r[1] for r in rows}

    # by_type
    rows = (await db.execute(
        select(SafetyEvent.event_type, func.count(SafetyEvent.id)).group_by(SafetyEvent.event_type)
    )).all()
    by_type = {r[0]: r[1] for r in rows}

    # last_30d
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    last_30d = (await db.execute(
        select(func.count(SafetyEvent.id)).where(SafetyEvent.occurred_at >= cutoff)
    )).scalar() or 0

    return StandardResponse(data=SafetyEventStats(
        total=total, by_status=by_status, by_severity=by_severity,
        by_type=by_type, last_30d=last_30d,
    ))


@router.get("/{event_id}", response_model=StandardResponse[SafetyEventOut], summary="安全事件详情")
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    ev = await db.get(SafetyEvent, event_id)
    if not ev:
        raise HTTPException(404, "事件不存在")
    # 权限: 非管理员只能看自己上报的
    if current.role != "admin" and ev.reporter_id != current.id:
        raise HTTPException(403, "无权访问此事件")
    return StandardResponse(data=await _serialize(db, ev))


@router.patch("/{event_id}", response_model=StandardResponse[SafetyEventOut], summary="更新事件状态/调查信息")
async def update_event(
    event_id: int,
    body: SafetyEventStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """管理员/质控员处理流转. 用户故事 #139 流程闭环."""
    if current.role not in {"admin"}:
        raise HTTPException(403, "仅管理员可处理事件")
    ev = await db.get(SafetyEvent, event_id)
    if not ev:
        raise HTTPException(404, "事件不存在")
    if body.status not in {"reported", "investigating", "resolved", "closed"}:
        raise HTTPException(400, "status 取值不合法")
    ev.status = body.status
    if body.handler_id is not None:
        ev.handler_id = body.handler_id
    else:
        ev.handler_id = ev.handler_id or current.id
    if body.root_cause is not None:
        ev.root_cause = body.root_cause
    if body.corrective_action is not None:
        ev.corrective_action = body.corrective_action
    if body.status in {"resolved", "closed"} and not ev.resolved_at:
        ev.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(ev)
    return StandardResponse(data=await _serialize(db, ev))
