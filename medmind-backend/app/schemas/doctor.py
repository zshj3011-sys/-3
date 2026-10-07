"""医生 Schema"""
from typing import Optional
from pydantic import BaseModel
from app.schemas.common import OrmBase


class DoctorOut(OrmBase):
    id: int
    doctor_name: str
    title: Optional[str] = None
    department_id: Optional[int] = None
    specialties: Optional[str] = None
    introduction: Optional[str] = None
    rating: Optional[float] = None
    years_of_practice: Optional[int] = None


class DepartmentOut(OrmBase):
    id: int
    code: str
    name: str
    description: Optional[str] = None
