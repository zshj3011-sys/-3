"""所有 SQLAlchemy ORM 模型"""
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.medical_record import MedicalRecord
from app.models.prescription import Prescription, PrescriptionItem
from app.models.appointment import Appointment
from app.models.ai_conversation import AIConversation, AIMessage
from app.models.drg import DRGCase
from app.models.lab_report import LabReport
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.safety_event import SafetyEvent          # v3.6.2
from app.models.research_dataset import ResearchDataset  # v3.6.2

__all__ = [
    "User", "Patient", "Doctor", "Department",
    "MedicalRecord", "Prescription", "PrescriptionItem",
    "Appointment", "AIConversation", "AIMessage",
    "DRGCase", "LabReport", "AuditLog", "Notification",
    "SafetyEvent", "ResearchDataset",
]
