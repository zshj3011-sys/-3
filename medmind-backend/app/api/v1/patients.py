"""患者管理 API"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientUpdate, PatientOut
from app.schemas.common import StandardResponse, PageResponse, PageMeta

router = APIRouter()


def _to_out(p: Patient) -> PatientOut:
    # 手动构造,避开 SQLAlchemy 实例上 .age 方法名冲突
    return PatientOut(
        id=p.id,
        real_name=p.real_name,
        id_card=p.id_card,
        birth_date=p.birth_date,
        gender=p.gender,
        phone=p.phone,
        address=p.address,
        allergy_history=p.allergy_history or [],
        past_history=p.past_history or [],
        emergency_contact=p.emergency_contact,
        health_summary=p.health_summary,
        age=p.age(),
    )


@router.post("/", response_model=StandardResponse[PatientOut], summary="创建患者档案")
async def create_patient(
    body: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    p = Patient(**body.model_dump(), user_id=current.id if current.role == "patient" else None)
    db.add(p)
    await db.flush()
    return StandardResponse(data=_to_out(p))


@router.get("/", response_model=PageResponse[PatientOut], summary="患者列表")
async def list_patients(
    keyword: Optional[str] = Query(None, description="姓名/身份证/手机号"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    stmt = select(Patient)
    count_stmt = select(func.count(Patient.id))
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where((Patient.real_name.like(like)) | (Patient.phone.like(like)))
        count_stmt = count_stmt.where((Patient.real_name.like(like)) | (Patient.phone.like(like)))

    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = stmt.order_by(Patient.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(stmt)).scalars().all()
    return PageResponse(
        data=[_to_out(p) for p in rows],
        meta=PageMeta(page=page, page_size=page_size, total=total,
                      total_pages=(total + page_size - 1) // page_size),
    )


@router.get("/{patient_id}", response_model=StandardResponse[PatientOut], summary="患者详情")
async def get_patient(patient_id: int, db: AsyncSession = Depends(get_db),
                       current: User = Depends(get_current_user)):
    p = await db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "患者不存在")
    return StandardResponse(data=_to_out(p))


@router.patch("/{patient_id}", response_model=StandardResponse[PatientOut], summary="更新患者")
async def update_patient(patient_id: int, body: PatientUpdate,
                         db: AsyncSession = Depends(get_db),
                         current: User = Depends(get_current_user)):
    p = await db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "患者不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    await db.flush()
    return StandardResponse(data=_to_out(p))


@router.delete("/{patient_id}", response_model=StandardResponse[dict], summary="删除患者")
async def delete_patient(patient_id: int, db: AsyncSession = Depends(get_db),
                          current: User = Depends(get_current_user)):
    p = await db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "患者不存在")
    await db.delete(p)
    return StandardResponse(data={"deleted": True})
