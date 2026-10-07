# MedMind Nexus · API 速查表

> 适用版本: **v3.6.3**（= v3.6.2 全集，含 v3.4 AI 辅助开方 / DRG 费用预警、v3.6 挂号 / 消息 / PRD 字面路径、v3.6.2 医疗安全事件 / 科研数据导入；v3.6.3 仅元数据收尾，API 完全不变）· 完整 OpenAPI 在线: `/docs` (Swagger) · `/redoc` (ReDoc)

## 通用约定

| 项 | 值 |
|---|---|
| Base URL | `http://localhost:8000` (开发) / `https://api.your-domain.com` (生产) |
| API 前缀 | `/v1` |
| 认证方式 | `Authorization: Bearer <access_token>` (JWT) |
| 响应包络 | `{ "code": 200, "message": "success", "data": ... }` |
| 错误响应 | `{ "code": 4xx/5xx, "message": "...", "detail": [...] }` |
| Content-Type | `application/json` (上传走 `multipart/form-data`) |

---

## 1. 认证 `/v1/auth`

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| POST | `/v1/auth/register` | 用户注册 | ❌ |
| POST | `/v1/auth/login` | 用户登录 (返回 access+refresh token) | ❌ |
| POST | `/v1/auth/refresh` | 刷新 Token | refresh token |
| POST | `/v1/auth/logout` | 登出 | ✅ |
| GET | `/v1/auth/me` | 获取当前用户 | ✅ |

**演示账号** (任选其一登录):

| username | password | role |
|---|---|---|
| `dr_zhang` | `doctor123` | 医生 |
| `admin` | `admin123` | 管理员 |
| `patient_li` | `patient123` | 患者 |
| `prof_zhao` | `researcher123` | 科研 |
| `pharm_wang` | `pharm123` | 药师 |

---

## 2. 患者 `/v1/patients`

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/v1/patients/` | 创建患者档案 |
| GET | `/v1/patients/?page=1&size=20&keyword=张` | 列表/搜索 |
| GET | `/v1/patients/{patient_id}` | 详情 |
| PATCH | `/v1/patients/{patient_id}` | 更新 |
| DELETE | `/v1/patients/{patient_id}` | 删除 |

## 3. 医生 / 科室

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/v1/doctors/` | 医生列表 |
| GET | `/v1/doctors/{doctor_id}` | 医生详情 |
| GET | `/v1/departments/` | 科室列表 |

---

## 4. AI 预问诊 `/v1/triage`

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/v1/triage/start` | 启动会话 (患者端入口) |
| POST | `/v1/triage/message` | 发送消息 (多轮) |
| GET | `/v1/triage/{session_id}/summary` | 获取 SOAP 摘要 |

请求示例:

```json
POST /v1/triage/start
{ "chief_complaint": "头痛3天伴发热" }
```

## 5. 病历 `/v1/records`

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/v1/records/ai-draft` | ✨ AI 生成 SOAP 病历草稿 (核心) |
| POST | `/v1/records/` | 保存病历 |
| GET | `/v1/records/?page=1&size=20` | 病历列表 |
| GET | `/v1/records/{rec_id}` | 病历详情 |
| POST | `/v1/records/{rec_id}/quality-check` | AI 病历质控 |
| POST | `/v1/records/{rec_id}/sign` | 医生电子签 |

## 6. 处方 `/v1/prescriptions`

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/v1/prescriptions/audit` | ✨ AI 处方审核 (双抗/相互作用/剂量) |
| POST | `/v1/prescriptions/suggest` | ✨ **v3.4** AI 辅助开方推荐 |
| POST | `/v1/prescriptions/` | 创建处方 (开方时自动审核入库) |
| GET | `/v1/prescriptions/?status=signed` | 处方列表 |
| GET | `/v1/prescriptions/{rx_id}` | 处方详情 |

## 7. DRG/DIP 控费 `/v1/drg`

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/v1/drg/predict` | ✨ DRG 分组+盈亏预测 |
| GET | `/v1/drg/cases` | 病案列表 |
| GET | `/v1/drg/dashboard` | DRG 看板汇总 |
| GET | `/v1/drg/cost-alert?alert_level=red\|yellow\|green` | ✨ **v3.4** 费用预警（可按级别筛选）|

## 8. 诊断辅助 / 报告解读 `/v1/reports`

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/v1/reports/interpret` | AI 报告解读 (检验/影像) |
| POST | `/v1/reports/diagnose` | ✨ 诊断辅助 (4 层幻觉防护) |

## 9. 科研 `/v1/research`

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/v1/research/literature/search` | 文献检索 (PubMed 风格) |
| POST | `/v1/research/grant/generate` | ✨ 国自然标书生成 (5 章节) |
| POST | `/v1/research/paper/polish` | 论文润色 (中→英 + 期刊适配) |
| POST | `/v1/research/statistics/recommend` | 统计方法推荐 + R 代码 |

## 10. 管理端 `/v1/admin`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/v1/admin/dashboard` | 运营驾驶舱 (5 KPI + 30 天趋势) |
| GET | `/v1/admin/quality` | 质控看板 (雷达图 6 维) |
| GET | `/v1/admin/ai-analytics` | AI 价值分析 |

## 11. WebSocket

| 端点 | 说明 |
|---|---|
| `WS /v1/ws/asr` | ✨ 实时语音转写流式（简化路径）|
| `WS /v1/ws/asr/stream` | ✨ **v3.6** PRD §9.1 字面路径 |
| `WS /v1/ws/ai-suggest` | ✨ AI 建议推送（简化路径）|
| `WS /v1/ws/ai/suggestions` | ✨ **v3.6** PRD §9.2 字面路径 |

**ASR 握手**: 连接成功后发送二进制 PCM 16k 帧, 服务端返回 JSON `{ "partial": "...", "final": false }`。

## 12. 挂号预约 `/v1/appointments` · **v3.6 新增**

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/v1/appointments/` | 在线挂号（含时段冲突检测）|
| GET | `/v1/appointments/?patient_id=&doctor_id=&date=&status=` | 多条件查询 |
| GET | `/v1/appointments/today?doctor_id={id}` | 医生今日预约（用户故事 #86 Must·MVP）|
| GET | `/v1/appointments/slots?department_id=&date=` | 可用号源（每时段 3 号，15 个时段）|
| PATCH | `/v1/appointments/{id}/cancel` | 取消预约 |
| PATCH | `/v1/appointments/{id}/check-in` | 到诊签到 |

## 13. 消息通知 `/v1/notifications` · **v3.6 新增**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/v1/notifications/?is_read=&category=&page=&size=` | 消息列表（筛选 + 分页）|
| GET | `/v1/notifications/unread-count` | 未读计数 + 分类聚合 |
| PATCH | `/v1/notifications/{id}/read` | 标记单条已读 |
| POST | `/v1/notifications/mark-all-read` | 全部已读 |
| POST | `/v1/notifications/` | 发送消息（管理员/医生权限）|

分类枚举：`appointment` / `medication` / `report` / `ai_alert` / `system`。

## 14. PRD 字面路径别名 `/v1/ai/*` · **v3.4 / v3.6 新增**

> 以下路径为客户 PRD 中出现的“字面 URL”，内部复用同一 Agent。为保证与客户 PRD 严格一致，同时保留“简化”与“字面”两种路径。

| 方法 | PRD 字面路径 | 简化路径（内部一致）| PRD 小节 |
|---|---|---|---|
| POST | `/v1/ai/consultation/generate-note` | `/v1/records/ai-draft` | §5.1 SOAP 生成 |
| POST | `/v1/ai/pre-consultation/{session_id}/message` | `/v1/triage/message` | §4.2 path-param 预问诊 |
| POST | `/v1/ai/pre-consultation/start` | `/v1/triage/start` | §4.1 |
| POST | `/v1/ai/prescriptions/suggest` | `/v1/prescriptions/suggest` | AI 辅助开方 |
| GET  | `/v1/ai/drg/cost-alert?alert_level=red` | `/v1/drg/cost-alert?alert_level=red` | DRG 费用预警 |

## 15. 医疗安全事件 `/v1/safety-events` · **v3.6.2 新增**

> PRD §07 用户故事地图 #139 (Must · V1.0)。上报→调查→整改→归档闭环。

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/v1/safety-events/` | 上报安全事件 |
| GET | `/v1/safety-events/?status=&severity=&event_type=&page=&page_size=` | 列表 (非管理员仅看自己上报的) |
| GET | `/v1/safety-events/stats` | 统计：by_status / by_severity / by_type + last_30d |
| GET | `/v1/safety-events/{id}` | 详情 |
| PATCH | `/v1/safety-events/{id}` | 更新状态/根因/整改措施（仅管理员）|

**事件类型枚举**：`medication_error`（用药差错）/ `fall`（跌倒）/ `surgical`（手术）/ `infection`（院感）/ `device_failure`（设备故障）/ `misdiagnosis`（误诊）/ `other`。

**严重程度**（国卸医疗质量安全分级）：`i` 警告事件 · `ii` 不良事件 · `iii` 未遂事件 · `iv` 隐患事件。

## 16. 科研数据导入 `/v1/research/datasets` · **v3.6.2 新增**

> PRD §07 用户故事地图 #165 (Must · V1.0)。支持 .csv / .xlsx 直读；.sav (SPSS) 在客户启用可选依赖 `pyreadstat` 后可用。

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/v1/research/datasets/upload` | 上传数据集 (multipart/form-data，表单字段：`file`、`name?`、`notes?`) |
| GET | `/v1/research/datasets/` | 我上传过的数据集列表（分页）|
| GET | `/v1/research/datasets/{id}/preview` | 获取 schema + 前 50 行预览 |
| DELETE | `/v1/research/datasets/{id}` | 删除数据集 |

**返回示例**：
```json
{
  "id": 3, "name": "pytest-csv", "file_format": "csv",
  "rows": 4, "columns": 5,
  "schema": [
    {"name":"patient_id","dtype":"int","null_count":0,"sample":"1"},
    {"name":"sex","dtype":"str","null_count":0,"sample":"M"},
    {"name":"hba1c","dtype":"float","null_count":3,"sample":"7.8"}
  ],
  "preview": [{...}, {...}]
}
```

**数据上限**：单文件 20 MB（演示默认）、预览 50 行。

## 17. 演示辅助 `/v1/demo`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/v1/demo/wechat-screens` | 微信小程序静态演示数据 |
| GET | `/v1/demo/doctor-schedule` | 医生今日排班 |

---

## 全局健康检查

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 `{ "status":"ok", ... }` |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |
| GET | `/web/sitemap.html` | 前端总览页 (同源挂载) |

---

## 调用示例 (curl)

```bash
# 1) 登录拿 token
TOKEN=$(curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"dr_zhang","password":"doctor123"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['access_token'])")

# 2) 调 AI 诊断
curl -s -X POST http://localhost:8000/v1/reports/diagnose \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"chief_complaint":"胸痛3小时","symptoms":["胸痛","胸闷","出汗"],"age":58,"sex":"male"}' \
  | python3 -m json.tool

# 3) DRG 预测
curl -s -X POST http://localhost:8000/v1/drg/predict \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"primary_diagnosis":"不稳定型心绞痛","icd10":"I20.0","age":58,"actual_cost":42000}'
```

---

## 标准响应包络

成功:
```json
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "request_id": "uuid"
}
```

失败 (校验):
```json
{
  "code": 422,
  "message": "请求参数校验失败",
  "detail": [
    { "type": "missing", "loc": ["body","patient_id"], "msg": "Field required" }
  ]
}
```

失败 (业务):
```json
{
  "code": 400,
  "message": "处方含禁忌组合, 请审核",
  "data": null
}
```

---

## 角色权限矩阵 (RBAC)

| 端点前缀 | patient | doctor | pharmacist | admin | researcher |
|---|---|---|---|---|---|
| `/v1/triage/*` | ✅ | ✅ | ❌ | ✅ | ❌ |
| `/v1/records/*` | 只读 | ✅ | ❌ | ✅ | 只读 |
| `/v1/prescriptions/audit` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `/v1/drg/*` | ❌ | ✅ | ❌ | ✅ | ❌ |
| `/v1/research/*` | ❌ | 只读 | ❌ | ✅ | ✅ |
| `/v1/admin/*` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `/v1/patients/*` | 仅自己 | ✅ | ❌ | ✅ | 脱敏 |

---

**版本**: **v3.6.3** · 更新于 2026-06-14 · 共 **60+ REST 路由 + 4 WebSocket**（含 PRD 字面别名 + v3.6.2 补齐 PRD §07 #139/#165；v3.6.3 路由零改动）

> v3.6 新增：挂号 6 + 消息 5 + PRD 字面路径 5 + 新 WS 2 = 18 个。
> v3.6.2 新增：安全事件 5 + 数据导入 4 = **9 个端点**（补齐 PRD §07 两个遗漏的 Must·V1.0 故事）。

## 变更历史

| 版本 | 时间 | 变更 |
|---|---|---|
| v1.0 | 2026-06-12 | 初版 40+ REST + 2 WS |
| v3.4 | 2026-06-13 中 | + `/prescriptions/suggest`、`/drg/cost-alert`、`/v1/ai/*` 部分别名 |
| v3.6 | 2026-06-13 晚 | + 挂号 6 + 消息 5 + PRD §5.1/§4.2/§9.1/§9.2 字面路径 + 新 WS 2 |
| **v3.6.2** | **2026-06-13 晚** | **+ 医疗安全事件上报 5 个 (PRD §07 #139) + 科研数据导入 4 个 (PRD §07 #165)** |
| **v3.6.3** | **2026-06-14** | **0 个新增端点**（仅交付包元数据收尾：Tauri 图标占位 + 文档版本号统一；API 完全沿用 v3.6.2）|
