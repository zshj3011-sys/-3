"""科研端 API - 文献/标书/论文润色"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.agents import ResearchAgent
from app.schemas.ai import (
    LiteratureSearchRequest, GrantOutlineRequest, GrantOutlineResponse,
)
from app.schemas.common import StandardResponse

router = APIRouter()
_agent = ResearchAgent()


@router.post("/literature/search", response_model=StandardResponse[dict],
             summary="AI 文献检索")
async def search_literature(body: LiteratureSearchRequest):
    data = await _agent.search_literature(
        body.query, body.sources, body.year_from, body.year_to
    )
    return StandardResponse(data=data)


@router.post("/grant/generate", response_model=StandardResponse[GrantOutlineResponse],
             summary="国自然标书 AI 生成")
async def generate_grant(body: GrantOutlineRequest):
    data = await _agent.generate_grant(
        body.title, body.grant_type, body.subject_code,
        body.keywords, body.research_basis,
    )
    return StandardResponse(data=GrantOutlineResponse(**data))


class PolishRequest(BaseModel):
    text: str


@router.post("/paper/polish", response_model=StandardResponse[dict],
             summary="论文中英润色 + 选刊推荐")
async def polish_paper(body: PolishRequest):
    data = await _agent.polish_paper(body.text)
    return StandardResponse(data=data)


class StatRequest(BaseModel):
    """统计分析: 选方法 + 生成 R 代码"""
    research_type: str  # cohort|case_control|cross_sectional|rct
    outcome_type: str   # binary|continuous|survival|categorical
    has_baseline_covariates: bool = False
    sample_size: int = 200


@router.post("/statistics/recommend", response_model=StandardResponse[dict],
             summary="统计方法推荐 + R 代码")
async def recommend_stats(body: StatRequest):
    method = "Cox 比例风险回归" if body.outcome_type == "survival" else (
        "Logistic 回归" if body.outcome_type == "binary" else (
            "线性混合效应模型" if body.has_baseline_covariates else "独立样本 t 检验/方差分析"
        )
    )
    r_code = (
        "# 1. 加载数据\nlibrary(survival); library(ggplot2)\n"
        "data <- read.csv('cohort.csv')\n\n"
        "# 2. 描述统计\nsummary(data)\n\n"
        f"# 3. {method}\n"
    )
    if body.outcome_type == "survival":
        r_code += (
            "fit <- survfit(Surv(time, status) ~ group, data = data)\n"
            "ggsurvplot(fit, pval = TRUE, risk.table = TRUE)\n\n"
            "# Cox 模型\ncox <- coxph(Surv(time, status) ~ group + age + sex, data = data)\nsummary(cox)\n"
        )
    elif body.outcome_type == "binary":
        r_code += "fit <- glm(outcome ~ exposure + age + sex, data = data, family = binomial)\nsummary(fit)\nexp(confint(fit))  # OR + 95%CI\n"
    else:
        r_code += "t.test(outcome ~ group, data = data)\n# 多组: aov(outcome ~ group, data) %>% summary\n"
    return StandardResponse(data={
        "recommended_method": method,
        "rationale": f"根据'{body.research_type}'设计与'{body.outcome_type}'结局,首选 {method}。",
        "r_code": r_code,
        "alternative_methods": ["Bootstrap", "倾向性评分匹配 PSM"],
    })
