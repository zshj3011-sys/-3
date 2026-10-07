"""API v1 路由聚合

v3.4 新增: PRD 兼容别名路由 (/ai/* 前缀) 以全量对齐 PRD 08 API 接口文档定义。
原有简化路由保留 (前端已适配), 同时提供 PRD 官方路径。
"""
from fastapi import APIRouter

from app.api.v1 import (
    auth, patients, doctors, departments,
    triage, records, prescriptions, drg, research,
    reports, admin, ws, demo, prd_compat,
    appointments, notifications,
    safety_events, research_datasets,  # v3.6.2 PRD #139 + #165
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(patients.router, prefix="/patients", tags=["患者管理"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["医生"])
api_router.include_router(departments.router, prefix="/departments", tags=["科室"])
api_router.include_router(triage.router, prefix="/triage", tags=["AI 预问诊"])
api_router.include_router(records.router, prefix="/records", tags=["病历"])
api_router.include_router(prescriptions.router, prefix="/prescriptions", tags=["处方"])
api_router.include_router(drg.router, prefix="/drg", tags=["DRG 控费"])
api_router.include_router(research.router, prefix="/research", tags=["科研"])
api_router.include_router(reports.router, prefix="/reports", tags=["报告解读"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理端"])
api_router.include_router(demo.router, prefix="/demo", tags=["演示数据"])
api_router.include_router(ws.router, tags=["WebSocket"])

# ===== v3.4 新增: PRD 兼容路由 (别名) =====
# 使 PRD 里定义的官方路径 (如 /ai/pre-consultation, /ai/drg/predict) 也可直接调用
api_router.include_router(triage.router, prefix="/ai/pre-consultation", tags=["PRD 兼容: AI 预问诊"])
api_router.include_router(prescriptions.router, prefix="/ai/prescriptions", tags=["PRD 兼容: 处方"])
api_router.include_router(drg.router, prefix="/ai/drg", tags=["PRD 兼容: DRG"])
api_router.include_router(research.router, prefix="/ai/research", tags=["PRD 兼容: 科研"])
api_router.include_router(reports.router, prefix="/ai/reports", tags=["PRD 兼容: 报告解读"])
api_router.include_router(records.router, prefix="/ai/medical-records", tags=["PRD 兼容: 病历"])
api_router.include_router(records.router, prefix="/medical-records", tags=["PRD 兼容: 病历 (非 AI)"])

# ===== v3.6 新增: PRD 字面路径全量对齐 + 新增挑没的模块 =====
api_router.include_router(prd_compat.router, tags=["PRD 兼容: 字面路径"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["挂号预约 (v3.6)"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["消息通知 (v3.6)"])

# ===== v3.6.2 新增: 补齐 PRD §07 两个被遗漏的 Must·V1.0 用户故事 =====
# #139 医疗安全事件上报、#165 科研数据导入 (Excel/CSV/SPSS)
api_router.include_router(safety_events.router, prefix="/safety-events", tags=["医疗安全事件 (v3.6.2)"])
api_router.include_router(research_datasets.router, prefix="/research/datasets", tags=["科研数据导入 (v3.6.2)"])
