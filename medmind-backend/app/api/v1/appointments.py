"""挂号预约 API — 实现 PRD 用户故事 #46 (挂号预约 · Must · V1.0)

提供患者在线挂号、查询、取消能力 + 医生查看今日预约 (Must · MVP).
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.user import User
from app.schemas.common import StandardResponse, PageResponse, PageMeta, OrmBase

router = APIRouter()


# ============== Schema ==============
class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    department_id: Optional[int] = None
    scheduled_at: datetime
    visit_type: str = Field(default="outpatient", description="outpatient|follow_up|emergency")
    chief_complaint: Optional[str] = None
    is_first_visit: Optional[bool] = True


class AppointmentOut(OrmBase):
    id: int
    patient_id: int
    doctor_id: int
    department_id: Optional[int]
    scheduled_at: datetime
    visit_type: str
    chief_complaint: Optional[str]
    triage_level: Optional[str]
    status: str
    is_first_visit: Optional[bool]
    ai_summary: Optional[str] = None
    # 关联展示用
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    department_name: Optional[str] = None


class AvailableSlot(BaseModel):
    doctor_id: int
    doctor_name: str
    department_name: str
    slot_time: datetime
    remaining: int  # 剩余号源


# ============== 端点 ==============
@router.post("/", response_model=StandardResponse[AppointmentOut], summary="创建预约挂号")
async def create_appointment(
    body: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """PRD 用户故事 #46: 患者在线挂号。"""
    # 校验患者 / 医生 / 时间
    patient = await db.get(Patient, body.patient_id)
    if not patient:
        raise HTTPException(404, "患者不存在")
    doctor = await db.get(Doctor, body.doctor_id)
    if not doctor:
        raise HTTPException(404, "医生不存在")

    # 简单冲突检查: 同医生同时段
    res = await db.execute(
        select(func.count(Appointment.id)).where(
            and_(
                Appointment.doctor_id == body.doctor_id,
                Appointment.scheduled_at == body.scheduled_at,
                Appointment.status.in_(("scheduled", "checked_in", "in_progress")),
            )
        )
    )
    conflicts = res.scalar() or 0
    if conflicts >= 1:
        raise HTTPException(409, "该时段已被占用, 请选择其它时间")

    appt = Appointment(
        patient_id=body.patient_id,
        doctor_id=body.doctor_id,
        department_id=body.department_id or doctor.department_id,
        scheduled_at=body.scheduled_at,
        visit_type=body.visit_type,
        chief_complaint=body.chief_complaint,
        is_first_visit=body.is_first_visit,
        status="scheduled",
    )
    db.add(appt)
    await db.flush()
    await db.refresh(appt)

    return StandardResponse(data=AppointmentOut(
        id=appt.id, patient_id=appt.patient_id, doctor_id=appt.doctor_id,
        department_id=appt.department_id, scheduled_at=appt.scheduled_at,
        visit_type=appt.visit_type, chief_complaint=appt.chief_complaint,
        triage_level=appt.triage_level, status=appt.status,
        is_first_visit=appt.is_first_visit, ai_summary=appt.ai_summary,
        patient_name=patient.real_name, doctor_name=doctor.doctor_name,
    ))


@router.get("/", response_model=PageResponse[AppointmentOut], summary="查询预约列表")
async def list_appointments(
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """支持患者查自己 / 医生查自己 / 按日期段筛选。"""
    stmt = select(Appointment, Patient, Doctor).join(
        Patient, Appointment.patient_id == Patient.id
    ).join(Doctor, Appointment.doctor_id == Doctor.id)

    if patient_id:
        stmt = stmt.where(Appointment.patient_id == patient_id)
    if doctor_id:
        stmt = stmt.where(Appointment.doctor_id == doctor_id)
    if status:
        stmt = stmt.where(Appointment.status == status)
    if date_from:
        stmt = stmt.where(Appointment.scheduled_at >= date_from)
    if date_to:
        stmt = stmt.where(Appointment.scheduled_at < date_to)
    stmt = stmt.order_by(Appointment.scheduled_at.desc())

    # 计数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # 分页
    res = await db.execute(stmt.offset((page - 1) * size).limit(size))
    items = []
    for appt, pat, doc in res.all():
        items.append(AppointmentOut(
            id=appt.id, patient_id=appt.patient_id, doctor_id=appt.doctor_id,
            department_id=appt.department_id, scheduled_at=appt.scheduled_at,
            visit_type=appt.visit_type, chief_complaint=appt.chief_complaint,
            triage_level=appt.triage_level, status=appt.status,
            is_first_visit=appt.is_first_visit, ai_summary=appt.ai_summary,
            patient_name=pat.real_name, doctor_name=doc.doctor_name,
        ))

    pages = (total + size - 1) // size if size else 0
    return PageResponse[AppointmentOut](
        data=items,
        meta=PageMeta(total=total, page=page, page_size=size, total_pages=pages),
    )


@router.get("/today", response_model=StandardResponse[list[AppointmentOut]],
            summary="医生今日预约 (用户故事 #86 Must·MVP)")
async def list_today(
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
    doctor_id: Optional[int] = None,
):
    """PRD 用户故事 #86: 医生查看今日预约。"""
    if not doctor_id:
        # 当前用户是医生 -> 自己的
        res = await db.execute(select(Doctor).where(Doctor.user_id == current.id))
        d = res.scalar_one_or_none()
        if d:
            doctor_id = d.id
        else:
            raise HTTPException(400, "请指定 doctor_id 或以医生身份登录")

    today_start = datetime.combine(datetime.now().date(), datetime.min.time())
    today_end = today_start + timedelta(days=1)

    stmt = select(Appointment, Patient, Doctor).join(
        Patient, Appointment.patient_id == Patient.id
    ).join(Doctor, Appointment.doctor_id == Doctor.id).where(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_at >= today_start,
            Appointment.scheduled_at < today_end,
        )
    ).order_by(Appointment.scheduled_at.asc())

    res = await db.execute(stmt)
    items = []
    for appt, pat, doc in res.all():
        items.append(AppointmentOut(
            id=appt.id, patient_id=appt.patient_id, doctor_id=appt.doctor_id,
            department_id=appt.department_id, scheduled_at=appt.scheduled_at,
            visit_type=appt.visit_type, chief_complaint=appt.chief_complaint,
            triage_level=appt.triage_level, status=appt.status,
            is_first_visit=appt.is_first_visit, ai_summary=appt.ai_summary,
            patient_name=pat.real_name, doctor_name=doc.doctor_name,
        ))
    return StandardResponse(data=items)


@router.get("/slots", response_model=StandardResponse[list[AvailableSlot]],
            summary="查询可用号源")
async def list_slots(
    db: AsyncSession = Depends(get_db),
    department_id: Optional[int] = None,
    date: Optional[datetime] = Query(None, description="查询日期, 默认明天"),
):
    """返回某科室某日可挂号的医生时段列表 (演示)。"""
    target_date = (date or (datetime.now() + timedelta(days=1))).date()
    base = datetime.combine(target_date, datetime.min.time())

    stmt = select(Doctor, Department).join(Department, Doctor.department_id == Department.id)
    if department_id:
        stmt = stmt.where(Doctor.department_id == department_id)
    stmt = stmt.limit(8)
    rows = (await db.execute(stmt)).all()

    slots: list[AvailableSlot] = []
    # 上午 9-11, 下午 14-17, 每位医生若干时段
    for doc, dept in rows:
        for hour in (9, 10, 14, 15, 16):
            t = base.replace(hour=hour, minute=0)
            # 计算该时段已占
            cnt = (await db.execute(
                select(func.count(Appointment.id)).where(
                    and_(Appointment.doctor_id == doc.id,
                         Appointment.scheduled_at == t,
                         Appointment.status.in_(("scheduled", "checked_in")))
                )
            )).scalar() or 0
            remaining = max(0, 3 - cnt)  # 每时段 3 个号
            if remaining > 0:
                slots.append(AvailableSlot(
                    doctor_id=doc.id,
                    doctor_name=doc.doctor_name,
                    department_name=dept.name,
                    slot_time=t,
                    remaining=remaining,
                ))
    return StandardResponse(data=slots)


@router.patch("/{appt_id}/cancel", response_model=StandardResponse[AppointmentOut],
              summary="取消预约")
async def cancel_appointment(
    appt_id: int,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    appt = await db.get(Appointment, appt_id)
    if not appt:
        raise HTTPException(404, "预约不存在")
    if appt.status in ("completed", "cancelled"):
        raise HTTPException(400, f"预约已 {appt.status}, 无法取消")
    appt.status = "cancelled"
    await db.flush()
    await db.refresh(appt)
    # 取关联展示数据
    pat = await db.get(Patient, appt.patient_id)
    doc = await db.get(Doctor, appt.doctor_id)
    return StandardResponse(data=AppointmentOut(
        id=appt.id, patient_id=appt.patient_id, doctor_id=appt.doctor_id,
        department_id=appt.department_id, scheduled_at=appt.scheduled_at,
        visit_type=appt.visit_type, chief_complaint=appt.chief_complaint,
        triage_level=appt.triage_level, status=appt.status,
        is_first_visit=appt.is_first_visit, ai_summary=appt.ai_summary,
        patient_name=pat.real_name if pat else None,
        doctor_name=doc.doctor_name if doc else None,
    ))


@router.patch("/{appt_id}/check-in", response_model=StandardResponse[AppointmentOut],
              summary="到诊签到")
async def check_in(
    appt_id: int,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    appt = await db.get(Appointment, appt_id)
    if not appt:
        raise HTTPException(404, "预约不存在")
    if appt.status != "scheduled":
        raise HTTPException(400, f"状态 {appt.status} 不可签到")
    appt.status = "checked_in"
    await db.flush()
    await db.refresh(appt)
    pat = await db.get(Patient, appt.patient_id)
    doc = await db.get(Doctor, appt.doctor_id)
    return StandardResponse(data=AppointmentOut(
        id=appt.id, patient_id=appt.patient_id, doctor_id=appt.doctor_id,
        department_id=appt.department_id, scheduled_at=appt.scheduled_at,
        visit_type=appt.visit_type, chief_complaint=appt.chief_complaint,
        triage_level=appt.triage_level, status=appt.status,
        is_first_visit=appt.is_first_visit, ai_summary=appt.ai_summary,
        patient_name=pat.real_name if pat else None,
        doctor_name=doc.doctor_name if doc else None,
    ))
