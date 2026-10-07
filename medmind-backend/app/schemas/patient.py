"""患者相关 Schema"""
from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.common import OrmBase


class PatientCreate(BaseModel):
    real_name: str = Field(..., min_length=1, max_length=50)
    id_card: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = Field(None, pattern="^(男|女|其他)$")
    phone: Optional[str] = None
    address: Optional[str] = None
    allergy_history: List[str] = []
    past_history: List[str] = []
    emergency_contact: Optional[dict] = None


class PatientUpdate(BaseModel):
    real_name: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    allergy_history: Optional[List[str]] = None
    past_history: Optional[List[str]] = None
    emergency_contact: Optional[dict] = None
    health_summary: Optional[str] = None


class PatientOut(OrmBase):
    id: int
    real_name: str
    id_card: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    allergy_history: Optional[List[str]] = []
    past_history: Optional[List[str]] = []
    emergency_contact: Optional[dict] = None
    health_summary: Optional[str] = None
    age: Optional[int] = None
