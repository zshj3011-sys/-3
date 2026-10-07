"""检验报告解读 API - 患者端"""
from fastapi import APIRouter

from app.services.agents import ReportInterpretAgent, DiagnosisAgent
from app.schemas.ai import (
    ReportInterpretRequest, ReportInterpretResponse,
    DiagnosisRequest, DiagnosisResponse, DifferentialDiagnosis,
)
from app.schemas.common import StandardResponse

router = APIRouter()
_report_agent = ReportInterpretAgent()
_dx_agent = DiagnosisAgent()


@router.post("/interpret", response_model=StandardResponse[ReportInterpretResponse],
             summary="AI 报告解读")
async def interpret(body: ReportInterpretRequest):
    data = await _report_agent.interpret(body.indicators, body.report_type or "blood_lipid")
    return StandardResponse(data=ReportInterpretResponse(**data))


@router.post("/diagnose", response_model=StandardResponse[DiagnosisResponse],
             summary="AI 诊断辅助 (鉴别诊断+幻觉防护)")
async def diagnose(body: DiagnosisRequest):
    data = await _dx_agent.differential(
        body.chief_complaint, body.symptoms, body.history, body.lab_results
    )
    # 转换主诊断为 DifferentialDiagnosis 类型
    pd = data.get("primary_diagnosis") or {}
    diffs = []
    for dd in data.get("differential_diagnoses", []):
        try:
            diffs.append(DifferentialDiagnosis(**dd))
        except Exception:
            pass
    resp = DiagnosisResponse(
        primary_diagnosis=DifferentialDiagnosis(**pd) if pd else DifferentialDiagnosis(
            diagnosis="待明确", probability=0.0, evidence=[]
        ),
        differential_diagnoses=diffs,
        hallucination_check=data.get("hallucination_check", {}),
        citations=data.get("citations", []),
        confidence=data.get("confidence", 0.0),
    )
    return StandardResponse(data=resp)
