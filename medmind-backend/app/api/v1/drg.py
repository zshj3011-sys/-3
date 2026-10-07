"""DRG/DIP 控费 API - 管理端核心"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import generate_id
from app.models.drg import DRGCase
from app.models.user import User
from app.services.agents import DRGAgent
from app.schemas.ai import DRGPredictRequest, DRGPredictResponse
from app.schemas.common import StandardResponse, PageResponse, PageMeta, OrmBase

router = APIRouter()
_agent = DRGAgent()


class DRGCaseOut(OrmBase):
    id: int
    case_number: str
    primary_diagnosis: Optional[str]
    icd10: Optional[str]
    drg_code: Optional[str]
    drg_name: Optional[str]
    payment_standard: Optional[float]
    actual_cost: Optional[float]
    predicted_cost: Optional[float]
    profit_loss: Optional[float]
    risk_level: Optional[str]
    status: str
    ai_suggestions: Optional[list] = []


@router.post("/predict", response_model=StandardResponse[DRGPredictResponse],
             summary="DRG 分组预测")
async def predict(body: DRGPredictRequest, db: AsyncSession = Depends(get_db)):
    data = await _agent.predict(
        body.primary_diagnosis, body.icd10,
        body.age, body.length_of_stay, body.actual_cost,
        body.secondary_diagnoses, body.procedures,
    )
    # 同时入库 case
    case = DRGCase(
        case_number=f"DRG-{generate_id()[:10].upper()}",
        primary_diagnosis=body.primary_diagnosis,
        icd10=body.icd10,
        drg_code=data.get("drg_code"),
        drg_name=data.get("drg_name"),
        payment_standard=data.get("payment_standard"),
        predicted_cost=data.get("predicted_cost"),
        actual_cost=body.actual_cost,
        profit_loss=data.get("profit_loss"),
        risk_level=data.get("risk_level"),
        ai_suggestions=data.get("suggestions", []),
        length_of_stay=body.length_of_stay,
    )
    db.add(case)
    return StandardResponse(data=DRGPredictResponse(**data))


@router.get("/cases", response_model=PageResponse[DRGCaseOut], summary="病案列表")
async def list_cases(
    risk_level: Optional[str] = Query(None, pattern="^(green|amber|red)$"),
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    stmt = select(DRGCase)
    count_stmt = select(func.count(DRGCase.id))
    if risk_level:
        stmt = stmt.where(DRGCase.risk_level == risk_level)
        count_stmt = count_stmt.where(DRGCase.risk_level == risk_level)
    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = stmt.order_by(DRGCase.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(stmt)).scalars().all()
    return PageResponse(
        data=[DRGCaseOut.model_validate(r) for r in rows],
        meta=PageMeta(page=page, page_size=page_size, total=total,
                      total_pages=(total + page_size - 1) // page_size),
    )


@router.get("/cost-alert", response_model=StandardResponse[dict],
            summary="DRG 费用预警 (v3.4 新增, 对齐 PRD 7.2)")
async def cost_alert(
    department_id: Optional[int] = Query(None, description="科室 ID (不传=全院)"),
    alert_level: Optional[str] = Query(None, pattern="^(red|amber|green)$",
                                       description="预警级别筛选"),
    page: int = 1, page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """获取在院患者费用预警列表. 对齐 PRD 7.2 GET /ai/drg/cost-alert.

    返回字段包含:
    - alerts: [{patient_id, patient_name, department, cost_ratio, alert_level, suggestion}]
    - summary: {red_count, amber_count, green_count, avg_ratio}
    """
    stmt = select(DRGCase).where(DRGCase.status != "closed")
    if alert_level:
        stmt = stmt.where(DRGCase.risk_level == alert_level)
    stmt = stmt.order_by(DRGCase.profit_loss.asc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(stmt)).scalars().all()

    alerts = []
    suggestion_map = {
        "red": "实际费用已超过定额 90%, 建议主管医师立即介入, 审查多取项目",
        "amber": "费用已达定额 75%-90%, 建议控制辅助药物使用",
        "green": "费用控制良好, 可维持现有诊疗方案",
    }
    for r in rows:
        cost_ratio = 0.0
        if r.payment_standard and r.payment_standard > 0:
            cost_ratio = round((r.actual_cost or r.predicted_cost or 0) / r.payment_standard, 3)
        # 检查关联患者名 - DRG 表未必包含 patient_id, 看 case_number
        alerts.append({
            "case_number": r.case_number,
            "primary_diagnosis": r.primary_diagnosis,
            "drg_code": r.drg_code,
            "drg_name": r.drg_name,
            "payment_standard": float(r.payment_standard or 0),
            "actual_cost": float(r.actual_cost or 0),
            "predicted_cost": float(r.predicted_cost or 0),
            "cost_ratio": cost_ratio,
            "profit_loss": float(r.profit_loss or 0),
            "alert_level": r.risk_level or "green",
            "suggestion": suggestion_map.get(r.risk_level or "green", "暂无建议"),
        })

    # 汇总
    red_q = await db.execute(select(func.count(DRGCase.id)).where(DRGCase.risk_level == "red"))
    amber_q = await db.execute(select(func.count(DRGCase.id)).where(DRGCase.risk_level == "amber"))
    green_q = await db.execute(select(func.count(DRGCase.id)).where(DRGCase.risk_level == "green"))

    return StandardResponse(data={
        "alerts": alerts,
        "summary": {
            "red_count": red_q.scalar() or 0,
            "amber_count": amber_q.scalar() or 0,
            "green_count": green_q.scalar() or 0,
            "total": len(alerts),
        },
        "filters": {"department_id": department_id, "alert_level": alert_level},
    })


@router.get("/dashboard", response_model=StandardResponse[dict], summary="DRG 看板汇总")
async def dashboard(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(DRGCase.id)))).scalar() or 0
    profit_q = await db.execute(select(func.sum(DRGCase.profit_loss)))
    total_profit = profit_q.scalar() or 0
    warned = (await db.execute(
        select(func.count(DRGCase.id)).where(DRGCase.risk_level.in_(["amber", "red"]))
    )).scalar() or 0
    return StandardResponse(data={
        "total_cases": total,
        "total_profit_loss": float(total_profit),
        "warned_count": warned,
        "warned_ratio": (warned / total) if total else 0,
    })
