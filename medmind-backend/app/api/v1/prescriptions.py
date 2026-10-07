"""处方 API - 含 AI 审核"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.security import generate_id
from app.models.prescription import Prescription, PrescriptionItem
from app.models.patient import Patient
from app.models.user import User
from app.services.agents import PrescriptionAuditAgent
from app.schemas.ai import PrescriptionAuditRequest, PrescriptionAuditResponse
from app.schemas.common import StandardResponse, PageResponse, PageMeta, OrmBase

router = APIRouter()
_audit_agent = PrescriptionAuditAgent()


class RxSuggestRequest(BaseModel):
    """v3.4 新增: AI 辅助开方请求体 - 对齐 PRD 6.1 /ai/prescriptions/suggest"""
    patient_id: Optional[int] = None
    diagnosis: List[str]
    allergy_history: Optional[List[str]] = None
    current_meds: Optional[List[str]] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None


class DrugSuggestion(BaseModel):
    drug_name: str
    dosage: str
    frequency: str
    duration: Optional[str] = None
    route: Optional[str] = None
    reason: Optional[str] = None
    contraindications: List[str] = []
    evidence_level: Optional[str] = None


class RxSuggestResponse(BaseModel):
    suggestions: List[DrugSuggestion]
    combined_warnings: List[str] = []
    alternatives: List[dict] = []
    citations: List[dict] = []


class RxItemIn(BaseModel):
    drug_name: str
    spec: Optional[str] = None
    dose: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    duration_days: Optional[int] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    note: Optional[str] = None
    ai_tag: Optional[str] = None


class RxCreate(BaseModel):
    patient_id: int
    doctor_id: Optional[int] = None
    medical_record_id: Optional[int] = None
    diagnosis: Optional[str] = None
    instructions: Optional[str] = None
    items: List[RxItemIn]


class RxItemOut(OrmBase):
    id: int
    drug_name: str
    spec: Optional[str]
    dose: Optional[str]
    frequency: Optional[str]
    route: Optional[str]
    duration_days: Optional[int]
    unit_price: Optional[float]
    ai_tag: Optional[str]


class RxOut(OrmBase):
    id: int
    rx_number: str
    patient_id: int
    doctor_id: int
    diagnosis: Optional[str]
    status: str
    total_amount: Optional[float]
    audit_score: Optional[float]
    audit_passed: Optional[bool]
    items: List[RxItemOut] = []


@router.post("/suggest", response_model=StandardResponse[RxSuggestResponse],
             summary="AI 辅助开方 (根据诊断推荐药物方案)")
async def suggest_prescription(body: RxSuggestRequest, db: AsyncSession = Depends(get_db),
                                current: User = Depends(get_current_user)):
    """v3.4 新增: 对齐 PRD 6.1 - AI 根据诊断列表生成推荐处方."""
    allergy = body.allergy_history or []
    age = body.patient_age
    gender = body.patient_gender
    # 自动填充患者信息
    if body.patient_id:
        p = await db.get(Patient, body.patient_id)
        if p:
            allergy = list({*(allergy), *(p.allergy_history or [])})
            age = age or p.age
            gender = gender or p.gender
    data = await _audit_agent.suggest(
        diagnosis=body.diagnosis,
        allergy_history=allergy,
        patient_age=age,
        patient_gender=gender,
        current_meds=body.current_meds or [],
    )
    return StandardResponse(data=RxSuggestResponse(**data))


@router.post("/audit", response_model=StandardResponse[PrescriptionAuditResponse],
             summary="AI 处方审核 (不入库)")
async def audit_only(body: PrescriptionAuditRequest, db: AsyncSession = Depends(get_db)):
    allergy = body.allergy_history
    # 补充患者过敏史
    p = await db.get(Patient, body.patient_id)
    if p and p.allergy_history:
        allergy = list({*(allergy or []), *(p.allergy_history or [])})
    data = await _audit_agent.audit(body.items, body.diagnosis or "", allergy)
    return StandardResponse(data=PrescriptionAuditResponse(**data))


@router.post("/", response_model=StandardResponse[RxOut], summary="创建处方")
async def create_rx(body: RxCreate, db: AsyncSession = Depends(get_db),
                    current: User = Depends(require_role("doctor"))):
    rx = Prescription(
        rx_number=f"RX-{generate_id()[:12].upper()}",
        patient_id=body.patient_id,
        doctor_id=body.doctor_id or current.id,
        medical_record_id=body.medical_record_id,
        diagnosis=body.diagnosis,
        instructions=body.instructions,
        items=[PrescriptionItem(**it.model_dump()) for it in body.items],
    )
    # 自动 AI 审核
    p = await db.get(Patient, body.patient_id)
    allergy = (p.allergy_history if p else []) or []
    audit = await _audit_agent.audit([it.model_dump() for it in body.items],
                                      body.diagnosis or "", allergy)
    rx.audit_score = audit.get("score")
    rx.audit_passed = audit.get("passed")
    rx.audit_warnings = audit.get("warnings", [])
    rx.ai_assisted = True

    # 估算总价
    total = sum((it.unit_price or 0) * (it.quantity or 1) for it in body.items)
    rx.total_amount = total

    db.add(rx)
    await db.flush()
    await db.refresh(rx, ["items"])
    return StandardResponse(data=RxOut.model_validate(rx))


@router.get("/", response_model=PageResponse[RxOut], summary="处方列表")
async def list_rx(patient_id: Optional[int] = None,
                  page: int = 1, page_size: int = 20,
                  db: AsyncSession = Depends(get_db),
                  current: User = Depends(get_current_user)):
    stmt = select(Prescription)
    count_stmt = select(func.count(Prescription.id))
    if patient_id:
        stmt = stmt.where(Prescription.patient_id == patient_id)
        count_stmt = count_stmt.where(Prescription.patient_id == patient_id)
    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = stmt.order_by(Prescription.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(stmt)).scalars().all()
    # 加载明细
    for r in rows:
        await db.refresh(r, ["items"])
    return PageResponse(
        data=[RxOut.model_validate(r) for r in rows],
        meta=PageMeta(page=page, page_size=page_size, total=total,
                      total_pages=(total + page_size - 1) // page_size),
    )


@router.get("/{rx_id}", response_model=StandardResponse[RxOut], summary="处方详情")
async def get_rx(rx_id: int, db: AsyncSession = Depends(get_db),
                 current: User = Depends(get_current_user)):
    r = await db.get(Prescription, rx_id)
    if not r:
        raise HTTPException(404, "处方不存在")
    await db.refresh(r, ["items"])
    return StandardResponse(data=RxOut.model_validate(r))
