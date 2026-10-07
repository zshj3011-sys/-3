"""医疗 AI Agent 服务层 - 对应 PRD M5 多Agent协作"""
from app.services.agents.triage import TriageAgent
from app.services.agents.soap import SOAPAgent
from app.services.agents.diagnosis import DiagnosisAgent
from app.services.agents.prescription import PrescriptionAuditAgent
from app.services.agents.drg import DRGAgent
from app.services.agents.report import ReportInterpretAgent
from app.services.agents.research import ResearchAgent

__all__ = [
    "TriageAgent", "SOAPAgent", "DiagnosisAgent",
    "PrescriptionAuditAgent", "DRGAgent",
    "ReportInterpretAgent", "ResearchAgent",
]
