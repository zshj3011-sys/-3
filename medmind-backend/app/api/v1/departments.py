"""科室 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.department import Department
from app.schemas.doctor import DepartmentOut
from app.schemas.common import StandardResponse

router = APIRouter()


@router.get("/", response_model=StandardResponse[list[DepartmentOut]], summary="科室列表")
async def list_departments(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Department).order_by(Department.id))).scalars().all()
    return StandardResponse(data=[DepartmentOut.model_validate(r) for r in rows])
