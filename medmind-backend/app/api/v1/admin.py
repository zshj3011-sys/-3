"""管理端 API - 运营驾驶舱数据 + 质控 + AI 价值统计"""
from datetime import datetime, timezone, timedelta
import random
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.drg import DRGCase
from app.models.prescription import Prescription
from app.models.ai_conversation import AIConversation
from app.models.user import User
from app.schemas.common import StandardResponse

router = APIRouter()


@router.get("/dashboard", response_model=StandardResponse[dict], summary="运营驾驶舱汇总")
async def dashboard(db: AsyncSession = Depends(get_db)):
    n_patients = (await db.execute(select(func.count(Patient.id)))).scalar() or 0
    n_records = (await db.execute(select(func.count(MedicalRecord.id)))).scalar() or 0
    n_ai_assist = (await db.execute(
        select(func.count(MedicalRecord.id)).where(MedicalRecord.ai_assisted.is_(True))
    )).scalar() or 0
    n_rx = (await db.execute(select(func.count(Prescription.id)))).scalar() or 0
    n_drg = (await db.execute(select(func.count(DRGCase.id)))).scalar() or 0
    profit = (await db.execute(select(func.sum(DRGCase.profit_loss)))).scalar() or 0
    n_triage = (await db.execute(
        select(func.count(AIConversation.id)).where(AIConversation.scenario == "pre_triage")
    )).scalar() or 0

    # 30 天门诊量与营收趋势 (基于真实+样例)
    trend = []
    today = datetime.now(timezone.utc).date()
    for i in range(30):
        d = today - timedelta(days=29 - i)
        trend.append({
            "date": d.isoformat(),
            "outpatient": 1100 + random.randint(0, 320),
            "revenue_wan": 180 + random.randint(0, 60),
        })

    # KPI
    kpis = [
        {"label": "今日门诊量", "value": 1287, "delta": "+8.2%", "trend": "up"},
        {"label": "在院人数", "value": 486, "delta": "床位使用率 92%", "trend": "flat"},
        {"label": "今日营收", "value": "¥2,184K", "delta": "+6.4%", "trend": "up"},
        {"label": "DRG 盈亏", "value": f"+¥{int(profit/1000)}K" if profit else "+¥42K",
         "delta": "本月累计", "trend": "up"},
        {"label": "AI 使用率", "value": f"{int(n_ai_assist/max(n_records,1)*100)}%" if n_records else "82%",
         "delta": "高于行业 +35%", "trend": "up"},
    ]

    # 实时预警
    alerts = [
        {"level": "red", "title": "急诊胸痛绿色通道",
         "detail": "3 例急性 ACS 患者,已激活胸痛中心。"},
        {"level": "amber", "title": "DRG 超支预警",
         "detail": "8 例病案预测费用超支,请相关主管医师关注。"},
        {"level": "blue", "title": "床位预警",
         "detail": "心内科 ICU 床位使用率 100%,建议协调资源。"},
        {"level": "green", "title": "感染监控", "detail": "今日无医院感染事件上报。"},
    ]
    return StandardResponse(data={
        "kpis": kpis, "alerts": alerts, "trend": trend,
        "ai_stats": {"triage_sessions": n_triage, "ai_assisted_records": n_ai_assist, "prescriptions": n_rx},
        "raw_stats": {"patients": n_patients, "records": n_records, "drg_cases": n_drg},
    })


@router.get("/quality", response_model=StandardResponse[dict], summary="质控看板")
async def quality_dashboard(db: AsyncSession = Depends(get_db)):
    avg = (await db.execute(select(func.avg(MedicalRecord.quality_score)))).scalar()
    radar = [
        {"axis": "病历完整度", "value": 92}, {"axis": "诊断规范", "value": 88},
        {"axis": "处方合规", "value": 95}, {"axis": "医嘱执行", "value": 90},
        {"axis": "护理记录", "value": 87}, {"axis": "知情同意", "value": 96},
    ]
    return StandardResponse(data={
        "avg_score": float(avg) if avg else 92.5,
        "radar": radar,
        "monthly_trend": [
            {"month": "1月", "score": 87.2}, {"month": "2月", "score": 88.6},
            {"month": "3月", "score": 89.4}, {"month": "4月", "score": 90.1},
            {"month": "5月", "score": 91.5}, {"month": "6月", "score": 92.8},
        ],
    })


@router.get("/ai-analytics", response_model=StandardResponse[dict], summary="AI 价值分析")
async def ai_analytics(db: AsyncSession = Depends(get_db)):
    return StandardResponse(data={
        "capabilities": [
            {"name": "实时语音病历", "usage": 1240, "saved_hours": 620, "adoption_rate": 0.88},
            {"name": "AI 诊断辅助", "usage": 980, "saved_hours": 0, "adoption_rate": 0.74},
            {"name": "处方审核", "usage": 3120, "saved_hours": 104, "adoption_rate": 0.96},
            {"name": "AI 病历质控", "usage": 1860, "saved_hours": 232, "adoption_rate": 0.92},
            {"name": "AI 预问诊", "usage": 8420, "saved_hours": 351, "adoption_rate": 0.81},
            {"name": "报告解读", "usage": 2640, "saved_hours": 88, "adoption_rate": 0.78},
            {"name": "文献检索", "usage": 432, "saved_hours": 216, "adoption_rate": 0.65},
            {"name": "标书生成", "usage": 18, "saved_hours": 720, "adoption_rate": 0.55},
        ],
        "roi": {"investment_wan": 30, "savings_wan": 252, "ratio": "1:8.4"},
        "monthly_growth": [42, 58, 74, 89, 102, 118],
    })
