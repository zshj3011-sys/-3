"""AI 服务端测试 - 覆盖预问诊/SOAP/诊断/处方/DRG/科研"""
import pytest


# ---- 预问诊完整链路 ----
@pytest.mark.asyncio
async def test_triage_full_flow(client):
    r = await client.post("/v1/triage/start", json={"chief_complaint": "胸口疼三天"})
    assert r.status_code == 200
    sid = r.json()["data"]["session_id"]
    assert sid

    # 模拟用户回答
    completed = False
    for msg in ["压榨样", "活动后", "有出汗", "有高血压", "吸烟"]:
        r = await client.post("/v1/triage/message", json={"session_id": sid, "message": msg})
        assert r.status_code == 200
        if r.json()["data"]["completed"]:
            completed = True
            break
    assert completed
    # 校验摘要
    r = await client.get(f"/v1/triage/{sid}/summary")
    summary = r.json()["data"]
    assert summary["suggested_department"]
    assert summary["triage_level"] in ("red", "yellow", "green")


# ---- SOAP 草稿 ----
@pytest.mark.asyncio
async def test_soap_draft(client, auth_headers):
    r = await client.post(
        "/v1/records/ai-draft",
        json={"patient_id": 1, "transcript": "对话转写: 患者胸痛 3 天劳累后明显"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["subjective"]
    assert d["assessment"]
    assert d["plan"]
    assert isinstance(d["icd10_codes"], list)
    assert d["confidence"] > 0


# ---- 诊断辅助 ----
@pytest.mark.asyncio
async def test_diagnosis(client, auth_headers):
    r = await client.post(
        "/v1/reports/diagnose",
        json={"chief_complaint": "胸痛", "symptoms": ["压榨样", "出汗"]},
        headers=auth_headers,
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["primary_diagnosis"]["diagnosis"]
    assert "hallucination_check" in d
    assert len(d["differential_diagnoses"]) > 0


# ---- 处方审核 ----
@pytest.mark.asyncio
async def test_prescription_audit(client, auth_headers):
    r = await client.post(
        "/v1/prescriptions/audit",
        json={
            "patient_id": 1,
            "diagnosis": "不稳定型心绞痛",
            "allergy_history": ["青霉素"],
            "items": [
                {"drug_name": "阿司匹林", "dose": "100mg", "frequency": "qd"},
                {"drug_name": "氯吡格雷", "dose": "75mg", "frequency": "qd"},
            ],
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert 0 <= d["score"] <= 100
    assert isinstance(d["warnings"], list)


# ---- DRG 预测 ----
@pytest.mark.asyncio
async def test_drg_predict(client, auth_headers):
    r = await client.post(
        "/v1/drg/predict",
        json={"primary_diagnosis": "不稳定型心绞痛", "icd10": "I20.0",
              "age": 56, "length_of_stay": 7, "actual_cost": 48500},
        headers=auth_headers,
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["drg_code"]
    assert d["risk_level"] in ("green", "amber", "red")


# ---- 报告解读 ----
@pytest.mark.asyncio
async def test_report_interpret(client):
    r = await client.post(
        "/v1/reports/interpret",
        json={"report_type": "blood_lipid",
              "indicators": [
                  {"name": "LDL-C", "value": 4.2, "unit": "mmol/L", "range": "<3.4"},
                  {"name": "TC", "value": 6.8, "unit": "mmol/L", "range": "<5.2"},
              ]},
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["summary"]
    assert d["urgency"] in ("normal", "attention", "urgent")


# ---- 文献检索 ----
@pytest.mark.asyncio
async def test_literature_search(client, auth_headers):
    r = await client.post(
        "/v1/research/literature/search",
        json={"query": "SGLT2", "sources": ["pubmed"], "page_size": 5},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert "results" in r.json()["data"]


# ---- 标书生成 ----
@pytest.mark.asyncio
async def test_grant_generate(client, auth_headers):
    r = await client.post(
        "/v1/research/grant/generate",
        json={"title": "SGLT2 在 CAD+T2DM 患者的机制研究",
              "grant_type": "面上项目"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["title"]
    assert len(d["sections"]) >= 3
    assert 0 <= d["overall_score"] <= 100


# ---- 管理端驾驶舱 ----
@pytest.mark.asyncio
async def test_admin_dashboard(client, auth_headers):
    r = await client.get("/v1/admin/dashboard", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()["data"]
    assert len(d["kpis"]) >= 4
    assert len(d["trend"]) == 30


# ---- 健康检查 ----
@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---- v3.4 新增: AI 辅助开方 (PRD 6.1) ----
@pytest.mark.asyncio
async def test_prescription_suggest(client, auth_headers):
    """PRD 6.1 - POST /ai/prescriptions/suggest"""
    r = await client.post(
        "/v1/prescriptions/suggest",
        json={
            "diagnosis": ["I20.0 不稳定型心绞痛", "I10 高血压"],
            "allergy_history": ["青霉素"],
            "patient_age": 58,
            "patient_gender": "male",
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert len(d["suggestions"]) >= 1
    first = d["suggestions"][0]
    assert first["drug_name"]
    assert first["dosage"]
    assert first["frequency"]
    # 应包含证据等级
    assert first.get("evidence_level")
    # 引用应包含指南
    assert len(d["citations"]) >= 1


# ---- v3.4 新增: AI 辅助开方 (PRD 兼容路径) ----
@pytest.mark.asyncio
async def test_prescription_suggest_prd_alias(client, auth_headers):
    """验证 PRD 官方路径 /ai/prescriptions/suggest 兼容性"""
    r = await client.post(
        "/v1/ai/prescriptions/suggest",
        json={"diagnosis": ["I20.0"], "patient_age": 58},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert len(r.json()["data"]["suggestions"]) >= 1


# ---- v3.4 新增: DRG 费用预警 (PRD 7.2) ----
@pytest.mark.asyncio
async def test_drg_cost_alert(client, auth_headers):
    """PRD 7.2 - GET /ai/drg/cost-alert"""
    r = await client.get("/v1/drg/cost-alert", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()["data"]
    assert "alerts" in d
    assert "summary" in d
    assert d["summary"]["total"] >= 0


# ---- v3.4 新增: DRG 费用预警 (PRD 兼容路径 + 筛选) ----
@pytest.mark.asyncio
async def test_drg_cost_alert_filter(client, auth_headers):
    """带 alert_level 筛选"""
    r = await client.get(
        "/v1/ai/drg/cost-alert?alert_level=red", headers=auth_headers
    )
    assert r.status_code == 200
    d = r.json()["data"]
    for a in d["alerts"]:
        assert a["alert_level"] == "red"


# ---- v3.4 新增: PRD 兼容路由全链路验证 ----
@pytest.mark.asyncio
async def test_prd_compat_routes(client, auth_headers):
    """验证 PRD 官方路径全部可用"""
    # 预问诊
    r = await client.post(
        "/v1/ai/pre-consultation/start",
        json={"chief_complaint": "胸痛"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    # DRG 预测
    r = await client.post(
        "/v1/ai/drg/predict",
        json={"primary_diagnosis": "急性心肌梗死", "icd10": "I21.0",
              "age": 60, "length_of_stay": 7, "actual_cost": 48000},
        headers=auth_headers,
    )
    assert r.status_code == 200
    # 文献检索
    r = await client.post(
        "/v1/ai/research/literature/search",
        json={"query": "SGLT2"},
        headers=auth_headers,
    )
    assert r.status_code == 200
