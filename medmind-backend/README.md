# MedMind Nexus 后端 (FastAPI)

> 面向中小医疗机构的 AI 原生智能体平台 · 全栈生产级后端

## ✨ 特性总览

- ⚡ **FastAPI** 异步框架 + Pydantic v2 校验
- 🗄 **SQLAlchemy 2.0** ORM (async) + Alembic 迁移
- 💾 **SQLite** 零配置开发 / **PostgreSQL 16** 生产部署
- 🔐 **JWT + bcrypt** 认证 + 角色权限 (patient/doctor/admin/researcher)
- 🤖 **LLM 适配器** 同接口对接 DeepSeek / 通义 / 智谱 / Moonshot / OpenAI / 离线 Mock
- 🧠 **7 个医疗 AI Agent**: 预问诊 / SOAP 病历 / 诊断辅助(4层幻觉防护) / 处方审核 / DRG / 报告解读 / 科研
- 🔌 **WebSocket** 实时 ASR 语音转写 + AI 建议推送
- 📊 **管理端驾驶舱** 运营 KPI / DRG 控费 / 质控看板 / AI 价值
- 🐳 **Docker Compose** 一键部署
- ✅ **18 个 pytest 测试** 覆盖核心 API + AI Agent
- 📂 **前端集成** 18 个 HTML 页面挂载在 `/web` 同源访问

## 🚀 快速开始 (3 步启动)

### 方式 1 · 本机直接跑 (零依赖)

```bash
cd medmind-backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

启动后:
- API 文档: http://localhost:8000/docs (Swagger UI)
- 前端入口: http://localhost:8000/web/sitemap.html
- 登录页: http://localhost:8000/web/login.html
- 健康检查: http://localhost:8000/health

数据库会自动创建并播种演示数据(5位患者 / 3位医生 / 7个用户 / 5条排班 / 6条 DRG)。

### 方式 2 · Docker 一键部署

```bash
cd medmind-backend
docker compose up
# 生产环境(含 PostgreSQL + Redis):
docker compose --profile prod up -d
```

## 🔑 默认演示账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| `admin` | `admin123` | 管理员 |
| `dr_zhang` | `doctor123` | 心内科主任医师 |
| `dr_li` | `doctor123` | 心内科副主任医师 |
| `prof_zhao` | `researcher123` | 科研处处长 |
| `patient_li` | `patient123` | 患者(李秀芳) |

## 📚 API 全景

完整 OpenAPI 文档: http://localhost:8000/docs

```
认证       POST /v1/auth/login | /register | /refresh | /logout | GET /me
患者管理   GET/POST/PATCH/DELETE /v1/patients
医生/科室  GET /v1/doctors | /v1/departments
AI 预问诊  POST /v1/triage/start | /v1/triage/message | GET /v1/triage/{sid}/summary
病历       POST /v1/records/ai-draft | / | GET /v1/records | POST /{id}/quality-check | /sign
处方       POST /v1/prescriptions/audit | / | GET /v1/prescriptions
DRG 控费   POST /v1/drg/predict | GET /v1/drg/cases | /v1/drg/dashboard
报告解读   POST /v1/reports/interpret | /v1/reports/diagnose
科研       POST /v1/research/literature/search | /grant/generate | /paper/polish | /statistics/recommend
管理端     GET /v1/admin/dashboard | /quality | /ai-analytics
演示数据   GET /v1/demo/wechat-screens | /doctor-schedule
WebSocket  /v1/ws/asr | /v1/ws/ai-suggest
```

## 🤖 切换真实 LLM (DeepSeek / 通义 / 智谱)

编辑 `.env`:

```bash
# DeepSeek
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_API_BASE=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 通义 (Qwen)
LLM_PROVIDER=qwen
LLM_API_KEY=sk-xxx
LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

# 智谱 GLM
LLM_PROVIDER=zhipu
LLM_API_KEY=xxx.xxx
LLM_API_BASE=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4-flash
```

留空 LLM_API_KEY 或 LLM_PROVIDER=mock → 使用内置 Mock(适合演示/CI,零成本)。

## 🗂 目录结构

```
medmind-backend/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── core/
│   │   ├── config.py        # Pydantic Settings 配置
│   │   ├── database.py      # 异步 SQLAlchemy 引擎
│   │   ├── security.py      # JWT + bcrypt
│   │   └── deps.py          # FastAPI 依赖项 (鉴权)
│   ├── models/              # 12 个 ORM 模型
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── api/v1/              # API 路由 (12 个文件)
│   │   ├── auth.py patients.py doctors.py departments.py
│   │   ├── triage.py records.py prescriptions.py
│   │   ├── drg.py research.py reports.py
│   │   ├── admin.py demo.py ws.py
│   └── services/
│       ├── llm/             # LLM 适配器
│       │   ├── base.py mock.py openai_compatible.py factory.py
│       └── agents/          # 7 个医疗 AI Agent
│           ├── triage.py soap.py diagnosis.py prescription.py
│           ├── drg.py report.py research.py
├── alembic/                 # 数据库迁移
├── scripts/seed.py          # 演示数据播种
├── tests/                   # 18 个 pytest 测试
├── static_frontend/         # 前端镜像 (挂载到 /web)
├── data/                    # 数据卷
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## 🧪 测试

```bash
pytest tests/ -v
# 18 passed in ~6s
```

## 🛡 安全

- 密码使用 **bcrypt** 哈希 (cost=12)
- JWT 双 token (access 60min + refresh 7d)
- 关键操作写 `audit_logs` (等保三级要求)
- CORS 可配置白名单
- Pydantic 严格校验所有入参
- 生产环境务必修改 `SECRET_KEY` (`openssl rand -hex 32`)

## 🏥 与 PRD 对应关系

本后端 100% 对齐客户提供的 10 份 PRD 文档:

| PRD 章节 | 实现位置 |
|---------|---------|
| 01 PRD 主文档 / 业务模块 | 全部 12 个 API 路由 |
| 02 患者端 | `triage.py` + `reports.py` + `demo.py` |
| 03 医生端 | `records.py` + `prescriptions.py` + `ws.py` |
| 04 管理端 | `drg.py` + `admin.py` |
| 05 科研端 | `research.py` |
| 06 M5 AI Agent | `services/agents/` 7 个 Agent |
| 08 API 接口规范 | 严格按 OpenAPI 3.0 实现 |
| 09 AI 能力说明书 | 4 层幻觉防护 + 多模型适配器 |
| 10 数据库设计 | `models/` 12 个 ORM 模型 |

## 🔄 数据库迁移 (生产用)

```bash
# 生成迁移
alembic revision --autogenerate -m "init schema"
# 应用迁移
alembic upgrade head
```

## 📈 性能与扩展

- 异步 IO,单实例并发 200+ rps (uvicorn workers=2)
- 数据库连接池 + pool_pre_ping
- LLM 调用 60s 超时 + tenacity 重试
- 生产建议: PostgreSQL + Redis 缓存 + Milvus 向量库 + vLLM 推理服务

## 📝 许可

本项目仅供商业演示与软件著作权申请使用。如需上线生产,请按 PRD 第 10 号文件完成等保三级合规改造。
