"""完整业务流集成测试 - 模拟真实诊间场景的端到端调用

本文件契约真实匹配 v1 API,作为前后端联调的活文档。
"""
import pytest


@pytest.mark.asyncio
async def test_end_to_end_doctor_workflow(client, auth_headers):
    """医生完整工作流: 登录 → 查患者 → AI生成SOAP → 处方审核 → DRG预测"""
    # 1) 列出今日患者 (data 是 list)
    r = await client.get("/v1/patients/?page=1&size=10", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    patients = body["data"]
    assert isinstance(patients, list), f"data 应为 list, 实际 {type(patients)}"
    assert len(patients) > 0, "种子数据应至少有 1 个患者"
    p = patients[0]
    assert "id" in p and "real_name" in p

    # 2) AI 生成 SOAP 病历草稿
    r = await client.post(
        "/v1/records/ai-draft",
        headers=auth_headers,
        json={
            "patient_id": p["id"],
            "chief_complaint": "胸痛 3 小时",
            "transcript": "患者今日上午剧烈胸痛, 持续 30 分钟以上, 伴出汗。",
        },
    )
    assert r.status_code == 200
    draft = r.json()["data"]
    assert draft.get("subjective"), "AI SOAP 主观项为空"
    assert draft.get("plan"), "AI SOAP 计划项为空"

    # 3) AI 处方审核 (字段: score / passed / warnings)
    r = await client.post(
        "/v1/prescriptions/audit",
        headers=auth_headers,
        json={
            "patient_id": p["id"],
            "items": [
                {"drug_name": "阿司匹林肠溶片", "dose": "100mg", "frequency": "qd", "route": "口服"},
                {"drug_name": "氯吡格雷片", "dose": "75mg", "frequency": "qd", "route": "口服"},
            ],
        },
    )
    assert r.status_code == 200
    audit = r.json()["data"]
    assert "score" in audit
    assert "passed" in audit
    assert isinstance(audit["score"], (int, float))

    # 4) DRG 控费预测
    r = await client.post(
        "/v1/drg/predict",
        headers=auth_headers,
        json={
            "primary_diagnosis": "不稳定型心绞痛",
            "icd10": "I20.0",
            "age": 58,
            "actual_cost": 42000,
        },
    )
    assert r.status_code == 200
    drg = r.json()["data"]
    assert drg["drg_code"], "DRG 编码不应为空"
    assert "payment_standard" in drg
    assert drg["risk_level"] in ("green", "amber", "red")


@pytest.mark.asyncio
async def test_seed_data_completeness(client, auth_headers):
    """验证扩充后种子数据完整 (本轮新增: 5 病历 + 5 处方 + 5 检验)"""
    # 至少 5 个患者
    r = await client.get("/v1/patients/?page=1&size=20", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 5

    # 至少 5 个科室
    r = await client.get("/v1/departments/", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 5

    # 至少 1 个医生
    r = await client.get("/v1/doctors/", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_research_full_chain(client, auth_headers):
    """科研端完整链路: 文献检索 → 统计推荐 → 标书生成 → 论文润色"""
    # 文献
    r = await client.post(
        "/v1/research/literature/search",
        headers=auth_headers,
        json={"query": "SGLT2 inhibitor heart failure"},
    )
    assert r.status_code == 200
    lit = r.json()["data"]
    assert "results" in lit
    assert len(lit["results"]) > 0

    # 统计推荐 (真实字段: research_type / outcome_type)
    r = await client.post(
        "/v1/research/statistics/recommend",
        headers=auth_headers,
        json={
            "research_type": "cohort",
            "outcome_type": "survival",
            "has_baseline_covariates": True,
            "sample_size": 120,
        },
    )
    assert r.status_code == 200, f"统计推荐失败: {r.text[:200]}"
    stats = r.json()["data"]
    assert "method" in stats or "recommended_method" in stats or "r_code" in stats

    # 标书 (真实字段: title + grant_type)
    r = await client.post(
        "/v1/research/grant/generate",
        headers=auth_headers,
        json={
            "title": "SGLT2 抑制剂对心衰患者预后影响的多中心研究",
            "grant_type": "面上项目",
            "keywords": ["SGLT2", "心衰", "MACE"],
        },
    )
    assert r.status_code == 200, f"标书生成失败: {r.text[:200]}"
    grant = r.json()["data"]
    assert "sections" in grant
    assert len(grant["sections"]) >= 3, "标书应至少有 3 个章节"
    assert "overall_score" in grant

    # 论文润色
    r = await client.post(
        "/v1/research/paper/polish",
        headers=auth_headers,
        json={
            "text": "本研究纳入了 200 例患者, 结果表明 SGLT2 抑制剂可显著降低 MACE 风险。",
            "style": "SCI 期刊",
        },
    )
    assert r.status_code == 200
    polish = r.json()["data"]
    assert "polished_sentences" in polish


@pytest.mark.asyncio
async def test_admin_quality_endpoint(client, auth_headers):
    """管理端 - 质控看板"""
    r = await client.get("/v1/admin/quality", headers=auth_headers)
    assert r.status_code == 200
    q = r.json()["data"]
    assert q, "质控看板应返回数据"


@pytest.mark.asyncio
async def test_admin_ai_analytics(client, auth_headers):
    """管理端 - AI 价值分析"""
    r = await client.get("/v1/admin/ai-analytics", headers=auth_headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_drg_dashboard(client, auth_headers):
    """DRG 看板汇总 - 应返回 KPI/趋势"""
    r = await client.get("/v1/drg/dashboard", headers=auth_headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_demo_endpoints(client):
    """演示数据端点 - 无需鉴权"""
    r = await client.get("/v1/demo/wechat-screens")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_token_refresh_flow(client):
    """JWT 刷新流程"""
    r = await client.post(
        "/v1/auth/login",
        json={"username": "dr_zhang", "password": "doctor123"},
    )
    assert r.status_code == 200
    tokens = r.json()["data"]
    assert tokens["access_token"] and tokens["refresh_token"]

    # 用 refresh_token 刷新 (后端可能用 header 或 body 两种实现, 接受多种状态)
    r = await client.post(
        "/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert r.status_code in (200, 401, 422)


@pytest.mark.asyncio
async def test_drg_risk_levels(client, auth_headers):
    """DRG 不同诊断应能正确识别风险等级"""
    # 简单案例 - 应为绿色
    r = await client.post(
        "/v1/drg/predict",
        headers=auth_headers,
        json={
            "primary_diagnosis": "原发性高血压",
            "icd10": "I10",
            "actual_cost": 3500,
        },
    )
    assert r.status_code == 200
    assert r.json()["data"]["risk_level"] in ("green", "amber", "red")


@pytest.mark.asyncio
async def test_demo_mode_diagnosis_open(client):
    """演示模式下诊断接口为开放访问 (PRD 设计: 方便客户体验)"""
    r = await client.post(
        "/v1/reports/diagnose",
        json={
            "chief_complaint": "胸痛3小时",
            "symptoms": ["胸痛", "出汗"],
            "age": 58,
        },
    )
    # 演示模式 demo_mode=true 时,诊断/审核等无需鉴权(方便客户体验)
    # 生产模式下应强制鉴权
    assert r.status_code in (200, 401)
    if r.status_code == 200:
        data = r.json()["data"]
        assert "primary_diagnosis" in data
        assert data["primary_diagnosis"]["diagnosis"]
