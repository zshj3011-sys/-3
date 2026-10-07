# MedMind Nexus 医智中枢 · 最终交付 (v3.6.3 收尾打包版，基于 v3.6.2 功能补齐版)

> 面向中小医疗机构的 AI 原生智能体平台 · **四端联动 · 全栈生产级**

![系统架构](docs/assets/architecture.png)

## 🚀 一键启动 (推荐 Makefile)

```bash
make install   # 安装后端依赖
make run       # 启动后端 (热重载)
# 另开终端
make smoke     # 跑 33 项联调冒烟测试
make test      # 跑 53 个 pytest 单元/集成测试
```

或经典三步:
```bash
cd medmind-backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

打开 **http://localhost:8000/web/sitemap.html** 进入全产品总览。

或 Docker 一键:`cd medmind-backend && docker compose up`

## 🔑 演示账号

| 用户名 | 密码 | 角色 |
|---|---|---|
| `dr_zhang` | `doctor123` | 医生 |
| `admin` | `admin123` | 管理员 |
| `patient_li` | `patient123` | 患者 |
| `prof_zhao` | `researcher123` | 科研 |
| `pharm_wang` | `pharm123` | 药师 |

## 📂 目录速览

| 目录 / 文件 | 内容 |
|---|---|
| [`MedMindNexus/`](MedMindNexus/) | **前端 Web** 19 个 HTML（18 业务页 + 1 sitemap 总览）— 4 端 + 官网 + v3.6 实时联通 |
| [`wechat-miniprogram/`](wechat-miniprogram/) | **原生微信小程序** 6 页面 + tabBar (**本轮新增**) |
| [`desktop-tauri/`](desktop-tauri/) | **PC 桌面端 Tauri 工程** (Win/Mac/Linux 跨平台, **本轮新增**) |
| [`medmind-backend/`](medmind-backend/) | **后端 FastAPI** + 53 pytest |
| [`scripts/`](scripts/) | 冒烟测试脚本 (33 项 API 自动验证) |
| [`docs/`](docs/) | 架构图 + API速查表 + **4份手册** (本轮新增 3 份) |
| [`.github/workflows/`](.github/workflows/) | CI/CD 配置 (pytest + lint + Docker + 小程序校验) |
| [`PRD原始需求文档/`](PRD原始需求文档/) | 客户原始 PRD 11 份 |
| [`任务清单.md`](任务清单.md) | 需求对称核对 + 完成度 |
| [`Makefile`](Makefile) | 一键命令 (install/run/test/smoke/docker, **本轮新增**) |

## ✅ 交付指标 (v3.6.2)

| 维度 | 指标 |
|---|---|
| **客户需求对称** | **31/31 (100%)**（含 v3.6 补齐挂号 + 消息 2 项核心模块）|
| **代码量** | 后端 ~4500 + 前端 3500+ + 小程序 ~1500 + 桌面端 ~200 = **9700+ 行** |
| **API 覆盖** | 50+ REST + 4 WebSocket（含 v3.6 PRD 字面路径 `/ws/asr/stream` & `/ws/ai/suggestions`） |
| **AI Agent** | 7 个 (预问诊/SOAP/诊断/处方/DRG/报告/科研) |
| **数据库** | **15 张表**（v3.6 新增 `notifications`）+ Alembic + 种子数据（5 病历 + 5 处方 + 5 检验报告 + 8 消息 + 5 预约）|
| **自动化测试** | **pytest 53/53 通过, 0 警告**（v3.6 42 + v3.6.2 +11）|
| **联调冒烟** | **33/33 项 API 真实可用（本轮已实测）** |
| **部署** | Docker / docker-compose + CI/CD pipeline |
| **文档** | OpenAPI + 11 份 PRD + 架构说明 + API速查表 + **4 份用户/运维/合规手册** |

## 🌟 v3.6 → v3.6.2 补齐推进

| 推进项 | 状态 |
|---|---|
| 补齐 PRD 用户故事 #46「挂号预约 Must·V1.0」—之前只有 model 无 API | ✅ 新增 6 个端点 |
| 补齐 PRD M1 患者端「消息通知」必备模块—之前完全缺失 | ✅ 新增表 + 5 个端点 + 种子数据 |
| PRD §5.1 字面路径 `POST /ai/consultation/generate-note` | ✅ 新增别名路由 |
| PRD §4.2 `POST /ai/pre-consultation/{sid}/message` path-param 形式 | ✅ 新增 |
| PRD §9.1/9.2 `WS /ws/asr/stream` / `/ws/ai/suggestions` 字面路径 | ✅ 新增 |
| 8 个之前纯静态的前端页面（diag/qc/records/admin×2/research×3）接通后端 | ✅ 新增 live-enhance.js |
| pytest | ✅ 33 → 42 → **53** (v3.6.2 复测 100% 通过) |
| smoke | ✅ 21 → 28 → **33** (v3.6.2 复测 100% 通过) |

> ⚠️ **诚实声明**：v3.5 及之前版本声称的「100% 对称」是模块层面的总览，并没有逆向对齐 PRD 字面 URL。v3.6 是对这些遗漏的真正补齐。

## 🌟 v3.5 (收尾) 推进

| 推进项 | 状态 |
|---|---|
| 顶层 `项目交付说明.md`（30 秒读懂入口） | ✅ 新增 |
| CSS 无障碍焦点环 (WCAG 2.4.7) | ✅ 新增 |
| CSS 减少动效偏好支持 | ✅ 新增 |
| CSS 打印样式（可一键导 PDF） | ✅ 新增 |
| 缓存清理（删除 `.pytest_cache` / `__pycache__`） | ✅ 完成 |
| 复跑实测验证 33 pytest + 21 smoke 全过 | ✅ 完成 |
| PRD 11 份与客户原始版本字节级 diff 校验 | ✅ 0 差异 |
| **本轮 0 新增功能**（遵循客户「不要画蛇添足」指示） | ✅ 严格遵守 |

## 🌟 上轮 (v3.1 → v3.2) 推进

| 推进项 | 状态 |
|---|---|
| 原生微信小程序工程 (6 页 + tabBar + api.js + demo.js) | ✅ 新增 |
| PC 桌面端 Tauri 2 配置 + 集成现有医生 Web | ✅ 新增 |
| 后端 seed 扩充 (5 病历 + 5 处方 + 5 检验报告) | ✅ 新增 |
| 集成测试 +10 用例 (test_integration.py) | ✅ 新增 (18→28) |
| 联调冒烟脚本 (16 项 API 实测全通过) | ✅ 新增 |
| GitHub Actions CI/CD (pytest + lint + Docker + miniprogram) | ✅ 新增 |
| Makefile 一键命令 | ✅ 新增 |
| 医生端使用手册 + 管理员手册 + 运维部署手册 + 合规说明 | ✅ 新增 |
| api.js 自动适配 Tauri 环境 | ✅ 改进 |
| sitemap.html 添加微信小程序/桌面端/手册卡片 | ✅ 改进 |

## 📖 推荐阅读顺序

1. **本 README** (5 分钟): 整体概览 + 启动
2. **[`任务清单.md`](任务清单.md)** (3 分钟): 看 **31 项需求**（含 v3.6 补齐的挂号+消息 + v3.6.2 补齐的安全事件+科研数据导入）逐一对照
3. **[`docs/screenshots/`](docs/screenshots/)** (3 分钟): 19 张全端真实截图速览 ★ v3.3 新增
4. **[`docs/验收测试报告.md`](docs/验收测试报告.md)** (5 分钟): 实测命令 + 输出证据 ★ v3.3 新增
5. **[`docs/上线检查清单.md`](docs/上线检查清单.md)** (10 分钟): 客户上线前打勾对照 ★ v3.3 新增
6. **[`docs/系统架构说明.md`](docs/系统架构说明.md)** (10 分钟): 四层架构 + 数据流
7. **[`docs/API速查表.md`](docs/API速查表.md)** (5 分钟): 40+ 路由速查
8. **[`docs/手册/`](docs/手册/)** (按需): 医生使用 / 管理员 / 运维 / 合规
9. **启动后** 访问 `/docs` 看完整 Swagger UI

---

**版本**: v3.6.3 (收尾打包版，基于 v3.6.2 功能补齐版) · **完成**: 2026-06-14 · **质量**: 0 业务代码占位符 · 0 断链 · 0 deprecated · **53 pytest + 33 冒烟 + 19 UI 截图 + 8 页实时联通 全通过**（v3.6.2 复测） · **PRD 11 份与客户原始版本字节级一致** · **v3.6.3 增量修复**：桌面端 Tauri 图标占位补齐 + 顶层文档版本号 v3.6.2 → v3.6.3 全面统一

> 注：`app/api/v1/ws.py` 内保留 1 处 `[ASR placeholder]` / `# TODO: 调用 Whisper/Azure ASR`——这是"切换真实模式时由客户决定使用 Whisper/Azure ASR"的占位钩子，mock 模式下不触发，已在 `docs/上线检查清单.md` 列入上线项；业务代码本身 0 占位符。
