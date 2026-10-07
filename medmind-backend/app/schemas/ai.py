"""AI 服务相关 Schema - 预问诊、SOAP生成、诊断辅助等"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from app.schemas.common import OrmBase


# ============ AI 预问诊 ============
class TriageStartRequest(BaseModel):
    patient_id: Optional[int] = None
    chief_complaint: Optional[str] = Field(None, description="主诉,可选;不填走自由对话")


class TriageMessageRequest(BaseModel):
    session_id: str
    message: str = Field(..., max_length=1000)


class AIMessageOut(BaseModel):
    role: str
    content: str
    quick_replies: Optional[List[str]] = None
    citations: Optional[List[dict]] = None


class TriageResponse(BaseModel):
    session_id: str
    ai_message: AIMessageOut
    step: int
    completed: bool = False
    summary: Optional[dict] = None  # 完成后给出 SOAP 摘要


class TriageSummary(BaseModel):
    session_id: str
    soap: dict  # {S, O, A, P}
    chief_complaint: str
    suggested_department: Optional[str] = None
    triage_level: Literal["red", "yellow", "green"]
    confidence: float
    suggested_doctors: List[dict] = []


# ============ SOAP 病历生成 ============
class SOAPGenerateRequest(BaseModel):
    patient_id: int
    transcript: Optional[str] = Field(None, description="语音转写文本,与pre_triage_session_id二选一")
    pre_triage_session_id: Optional[str] = None
    additional_context: Optional[str] = None


class SOAPDraft(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str
    icd10_codes: List[str] = []
    confidence: float
    citations: List[dict] = []
    quality_warnings: List[str] = []


# ============ AI 诊断辅助 ============
class DiagnosisRequest(BaseModel):
    chief_complaint: str
    symptoms: List[str] = []
    history: Optional[str] = None
    lab_results: Optional[List[dict]] = None
    patient_id: Optional[int] = None


class DifferentialDiagnosis(BaseModel):
    diagnosis: str
    icd10: Optional[str] = None
    probability: float
    evidence: List[str]
    against: List[str] = []
    recommended_tests: List[str] = []


class DiagnosisResponse(BaseModel):
    primary_diagnosis: DifferentialDiagnosis
    differential_diagnoses: List[DifferentialDiagnosis]
    hallucination_check: dict  # 4层幻觉防护结果
    citations: List[dict]
    confidence: float


# ============ 处方审核 ============
class PrescriptionAuditRequest(BaseModel):
    patient_id: int
    diagnosis: Optional[str] = None
    allergy_history: List[str] = []
    items: List[dict]  # [{drug_name, dose, frequency, route, ...}]


class AuditWarning(BaseModel):
    level: Literal["info", "warn", "error"]
    category: str  # 剂量|相互作用|过敏|禁忌|配伍
    title: str
    detail: str
    related_drugs: List[str] = []


class PrescriptionAuditResponse(BaseModel):
    score: float  # 0-100
    passed: bool
    warnings: List[AuditWarning]
    suggestions: List[str]
    citations: List[dict] = []


# ============ DRG 控费 ============
class DRGPredictRequest(BaseModel):
    primary_diagnosis: str
    icd10: Optional[str] = None
    secondary_diagnoses: List[str] = []
    procedures: List[str] = []
    age: Optional[int] = None
    gender: Optional[str] = None
    length_of_stay: Optional[int] = None
    actual_cost: Optional[float] = None


class DRGPredictResponse(BaseModel):
    drg_code: str
    drg_name: str
    payment_standard: float
    predicted_cost: float
    profit_loss: float
    risk_level: Literal["green", "amber", "red"]
    suggestions: List[str]


# ============ 报告解读 ============
class ReportInterpretRequest(BaseModel):
    indicators: List[dict] = []  # [{name, value, unit, range}]
    patient_id: Optional[int] = None
    report_type: Optional[str] = "blood_lipid"


class ReportInterpretResponse(BaseModel):
    summary: str
    abnormal_indicators: List[dict]
    plain_language_interpretation: str
    suggestions: List[str]
    urgency: Literal["normal", "attention", "urgent"]


# ============ 文献检索 ============
class LiteratureSearchRequest(BaseModel):
    query: str
    sources: List[str] = ["pubmed", "cnki"]
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    page: int = 1
    page_size: int = 10


class Literature(BaseModel):
    title: str
    authors: List[str]
    journal: str
    year: int
    impact_factor: Optional[float] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    abstract: str
    ai_summary: str
    tags: List[str] = []


# ============ 标书生成 ============
class GrantOutlineRequest(BaseModel):
    title: str
    grant_type: str = "面上项目"
    subject_code: Optional[str] = None
    keywords: List[str] = []
    research_basis: Optional[str] = None


class GrantSection(BaseModel):
    section: str
    title: str
    content: str
    ai_score: Optional[int] = None
    suggestions: List[str] = []


class GrantOutlineResponse(BaseModel):
    title: str
    sections: List[GrantSection]
    overall_score: int
    citations: List[dict]
