"""病历 API - 含 AI 生成 SOAP 草稿、质控"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.ai_conversation import AIConversation
from app.models.user import User
from app.services.agents import SOAPAgent
from app.schemas.ai import SOAPGenerateRequest, SOAPDraft
from app.schemas.common import StandardResponse, PageResponse, PageMeta, OrmBase

router = APIRouter()
_soap_agent = SOAPAgent()


class RecordCreate(BaseModel):
    patient_id: int
    doctor_id: Optional[int] = None
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    icd10_codes: list[str] = []
    record_type: str = "outpatient"
    ai_assisted: bool = False
    ai_draft_raw: Optional[str] = None


class RecordOut(OrmBase):
    id: int
    patient_id: int
    doctor_id: Optional[int]
    subjective: Optional[str]
    objective: Optional[str]
    assessment: Optional[str]
    plan: Optional[str]
    icd10_codes: Optional[list] = []
    record_type: str
    status: str
    ai_assisted: bool
    quality_score: Optional[float] = None
    quality_issues: Optional[list] = []
    chief_complaint: Optional[str] = None


@router.post("/ai-draft", response_model=StandardResponse[SOAPDraft], summary="AI 生成病历草稿")
async def ai_draft(body: SOAPGenerateRequest, db: AsyncSession = Depends(get_db),
                   current: User = Depends(get_current_user)):
    # 加载患者背景
    p = await db.get(Patient, body.patient_id)
    if not p:
        raise HTTPException(404, "患者不存在")
    patient_ctx = (
        f"姓名: {p.real_name}, 性别: {p.gender}, 年龄: {p.age()}, "
        f"过敏史: {p.allergy_history or '无'}, 既往史: {p.past_history or '无'}"
    )
    # 优先用 pre_triage 摘要
    transcript = body.transcript or ""
    if body.pre_triage_session_id:
        res = await db.execute(select(AIConversation).where(
            AIConversation.session_id == body.pre_triage_session_id))
        conv = res.scalar_one_or_none()
        if conv and conv.soap_summary:
            s = conv.soap_summary
            transcript = f"预问诊摘要: S={s.get('S','')} O={s.get('O','')} A={s.get('A','')} P={s.get('P','')}\n\n{transcript}"
    if body.additional_context:
        transcript += "\n" + body.additional_context
    if not transcript.strip():
        raise HTTPException(400, "transcript 与 pre_triage_session_id 至少二选一")

    data = await _soap_agent.generate_draft(transcript, patient_ctx)
    return StandardResponse(data=SOAPDraft(**data))


@router.post("/", response_model=StandardResponse[RecordOut], summary="保存病历")
async def save_record(body: RecordCreate, db: AsyncSession = Depends(get_db),
                      current: User = Depends(get_current_user)):
    if current.role not in ("doctor", "admin"):
        raise HTTPException(403, "仅医生可创建病历")
    rec = MedicalRecord(
        **body.model_dump(),
        chief_complaint=(body.subjective or "")[:255],
    )
    db.add(rec)
    await db.flush()
    return StandardResponse(data=RecordOut.model_validate(rec))


@router.get("/", response_model=PageResponse[RecordOut], summary="病历列表")
async def list_records(
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    stmt = select(MedicalRecord)
    count_stmt = select(func.count(MedicalRecord.id))
    if patient_id:
        stmt = stmt.where(MedicalRecord.patient_id == patient_id)
        count_stmt = count_stmt.where(MedicalRecord.patient_id == patient_id)
    if doctor_id:
        stmt = stmt.where(MedicalRecord.doctor_id == doctor_id)
        count_stmt = count_stmt.where(MedicalRecord.doctor_id == doctor_id)
    if status_filter:
        stmt = stmt.where(MedicalRecord.status == status_filter)
        count_stmt = count_stmt.where(MedicalRecord.status == status_filter)
    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = stmt.order_by(MedicalRecord.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(stmt)).scalars().all()
    return PageResponse(
        data=[RecordOut.model_validate(r) for r in rows],
        meta=PageMeta(page=page, page_size=page_size, total=total,
                      total_pages=(total + page_size - 1) // page_size),
    )


@router.get("/{rec_id}", response_model=StandardResponse[RecordOut], summary="病历详情")
async def get_record(rec_id: int, db: AsyncSession = Depends(get_db),
                     current: User = Depends(get_current_user)):
    r = await db.get(MedicalRecord, rec_id)
    if not r:
        raise HTTPException(404, "病历不存在")
    return StandardResponse(data=RecordOut.model_validate(r))


@router.post("/{rec_id}/quality-check", response_model=StandardResponse[dict],
             summary="AI 病历质控检查")
async def quality_check(rec_id: int, db: AsyncSession = Depends(get_db),
                        current: User = Depends(get_current_user)):
    r = await db.get(MedicalRecord, rec_id)
    if not r:
        raise HTTPException(404, "病历不存在")
    # 简化质控规则: 字段齐全度 + ICD-10 + 长度
    issues = []
    score = 100.0
    if not r.subjective:
        issues.append({"level": "error", "title": "缺少主观信息(S)"}); score -= 25
    if not r.objective:
        issues.append({"level": "warn", "title": "缺少客观查体(O)"}); score -= 15
    if not r.assessment:
        issues.append({"level": "error", "title": "缺少评估诊断(A)"}); score -= 25
    if not r.plan:
        issues.append({"level": "warn", "title": "缺少治疗计划(P)"}); score -= 15
    if not r.icd10_codes:
        issues.append({"level": "info", "title": "建议补充 ICD-10 编码"}); score -= 5
    r.quality_score = max(score, 0.0)
    r.quality_issues = issues
    await db.flush()
    return StandardResponse(data={
        "quality_score": r.quality_score, "issues": issues, "passed": r.quality_score >= 80
    })


@router.post("/{rec_id}/sign", response_model=StandardResponse[RecordOut],
             summary="医生签字提交病历")
async def sign_record(rec_id: int, db: AsyncSession = Depends(get_db),
                      current: User = Depends(require_role("doctor"))):
    from datetime import datetime, timezone
    r = await db.get(MedicalRecord, rec_id)
    if not r:
        raise HTTPException(404, "病历不存在")
    r.status = "signed"
    r.signed_at = datetime.now(timezone.utc).isoformat()
    await db.flush()
    return StandardResponse(data=RecordOut.model_validate(r))
