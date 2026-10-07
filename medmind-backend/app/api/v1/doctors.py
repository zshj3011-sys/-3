"""医生列表 API"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.doctor import Doctor
from app.schemas.doctor import DoctorOut
from app.schemas.common import StandardResponse

router = APIRouter()


@router.get("/", response_model=StandardResponse[list[DoctorOut]], summary="医生列表")
async def list_doctors(
    department_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Doctor)
    if department_id:
        stmt = stmt.where(Doctor.department_id == department_id)
    if keyword:
        stmt = stmt.where(Doctor.doctor_name.like(f"%{keyword}%"))
    rows = (await db.execute(stmt)).scalars().all()
    return StandardResponse(data=[DoctorOut.model_validate(d) for d in rows])


@router.get("/{doctor_id}", response_model=StandardResponse[DoctorOut], summary="医生详情")
async def get_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)):
    d = await db.get(Doctor, doctor_id)
    if not d:
        raise HTTPException(404, "医生不存在")
    return StandardResponse(data=DoctorOut.model_validate(d))
