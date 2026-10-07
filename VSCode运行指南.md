# 医智中枢 · VSCode 运行指南

> 生成时间：2026-10-07 · 已在你电脑上配置完毕，照此操作即可

---

## 一、你的电脑环境现状（已检测完毕）

| 工具 | 版本 | 状态 |
|------|------|------|
| Python | 3.12.7 (Anaconda) | ✅ 已就绪 |
| pip | 26.2.1 | ✅ 已修复（原 Anaconda base 环境的 pip 模块缺失，已用 `conda install pip` 修复） |
| Node.js | v22.16.0 | ✅ 已就绪（本项目后端不需要，仅 Tauri 桌面端/前端工具链可能用到） |
| VSCode | 1.108.2 | ✅ 已就绪 |
| Git | 未安装 | ⚠️ 不影响运行项目；如需版本控制请另装 |
| Docker | 未安装 | ⚠️ 不影响；Docker 只是可选部署方式 |
| Rust/Cargo | 未安装 | ⚠️ 不影响；仅 Tauri 桌面端需要，Web 后端运行不需要 |

**后端 Python 依赖（requirements.txt 中的 20+ 个包）已全部安装到 Anaconda base 环境。**

---

## 二、项目架构速览

```
医智中枢/
├── medmind-backend/      ← Python FastAPI 后端（★ 你要运行的核心）
│   ├── app/main.py       ← 入口文件
│   ├── .env              ← 环境配置（已从 .env.example 复制好）
│   └── requirements.txt  ← 依赖清单（已安装）
├── MedMindNexus/         ← 纯 HTML/CSS/JS 前端（由后端挂载到 /web）
├── desktop-tauri/        ← Tauri 桌面端工程（可选，运行需 Rust）
├── wechat-miniprogram/   ← 微信小程序源码（需微信开发者工具）
└── .vscode/              ← VSCode 配置（已为你创建好）
    ├── launch.json       ← 调试配置（按 F5 启动后端）
    ├── tasks.json        ← 任务（安装依赖/启动/测试/播种）
    └── settings.json     ← 工作区设置
```

**技术栈**：后端 FastAPI + SQLAlchemy + SQLite（零配置本地数据库） + Pydantic v2
**AI 模式**：默认 `LLM_PROVIDER=mock`，无需 API Key 即可演示

---

## 三、在 VSCode 中打开项目

### 步骤 1：打开项目文件夹

1. 启动 VSCode
2. `文件` 菜单 → `打开文件夹...`
3. 选择 `D:\Desktop\医智中枢` → 点击「选择文件夹」

**⚠️ 重要**：要打开**项目根目录** `D:\Desktop\医智中枢`，不是 `medmind-backend` 子目录。这样 VSCode 才能读到 `.vscode/` 里的配置。

### 步骤 2：确认 Python 解释器

1. 按 `Ctrl+Shift+P` 打开命令面板
2. 输入并选择 `Python: 选择解释器`
3. 选择带 `Anaconda` 字样的那条：`Python 3.12.7 ('base')  D:\anaconda3\python.exe`

如果列表里没有，点「输入解释器路径」→「查找」，手动选 `D:\anaconda3\python.exe`。

---

## 四、运行后端（3 种方式，任选其一）

### 方式 A：按 F5 调试模式启动（推荐）

1. 打开任意 `.py` 文件（比如 `medmind-backend/app/main.py`）
2. 按 `F5`（或左侧调试面板的绿色三角）
3. 选择配置「启动 MedMind 后端 (uvicorn 热重载)」
4. 终端会输出 uvicorn 启动日志，看到：
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```
   表示启动成功。

**优点**：可以直接打断点调试代码。

### 方式 B：任务菜单启动

1. `Ctrl+Shift+P` → 输入 `Tasks: 运行任务`
2. 选择「启动后端 (热重载)」
3. 终端会显示启动日志。

### 方式 C：终端手动启动

1. `` Ctrl+` `` 打开 VSCode 内置终端
2. 执行：
   ```powershell
   cd D:\Desktop\医智中枢\medmind-backend
   $env:PYTHONPATH = (Get-Location).Path
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## 五、访问项目

后端启动后，浏览器打开以下地址：

| 入口 | URL |
|------|-----|
| **全产品总览**（推荐第一站） | http://localhost:8000/web/sitemap.html |
| 官网首页 | http://localhost:8000/web/index.html |
| 登录页 | http://localhost:8000/web/login.html |
| API 文档 Swagger | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |

### 演示账号

| 用户名 | 密码 | 角色 |
|---|---|---|
| `dr_zhang` | `doctor123` | 医生 |
| `admin` | `admin123` | 管理员 |
| `patient_li` | `patient123` | 患者 |
| `prof_zhao` | `researcher123` | 科研 |
| `pharm_wang` | `pharm123` | 药师 |

---

## 六、常用操作

### 运行测试
- `Ctrl+Shift+P` → `Tasks: 运行任务` → 「运行 pytest 测试」
- 或终端：
  ```powershell
  cd D:\Desktop\医智中枢\medmind-backend
  $env:PYTHONPATH = (Get-Location).Path
  pytest tests/ -v
  ```

### 重新播种演示数据（清空当前数据库重建）
- `Ctrl+Shift+P` → `Tasks: 运行任务` → 「重新播种演示数据」
- 或手动删除 `medmind-backend\data\medmind.db` 后重启后端，会自动播种。

### 停止后端
- 终端按 `Ctrl+C`

---

## 七、可能遇到的问题

### Q1：终端中文乱码
日志里患者姓名等中文显示为乱码——这是 PowerShell 的 GBK 编码与 Python 输出冲突，**不影响功能**，只是日志显示问题。后端 API 返回的 JSON 中文是正常的 UTF-8。

如想改善，在终端执行：
```powershell
chcp 65001
```

### Q2：bcrypt 版本警告
日志里出现 `(trapped) error reading bcrypt version`——这是 passlib 4.2 + bcrypt 4.2 的已知兼容警告，**不影响密码功能**，可忽略。

### Q3：端口被占用
如果 8000 端口被其他程序占用，改启动命令的 `--port 8000` 为 `--port 8001` 等空闲端口。同时修改 `.env` 里的 `CORS_ORIGINS`。

### Q4：pip 相关错误
你的 Anaconda base 环境的 pip 曾缺失，已修复。如果再次出现 `No module named pip`，执行：
```powershell
conda install -n base pip
```

### Q5：想用真实 LLM（而非 Mock）
编辑 `medmind-backend/.env`：
```
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-你的key
LLM_API_BASE=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```
留空或保持 `mock` 则用内置 Mock 演示数据（零成本）。

---

## 八、其他子项目（可选）

| 子项目 | 用途 | 运行所需 |
|--------|------|----------|
| `MedMindNexus/` | 纯 HTML 前端 | 后端启动后直接通过 `/web` 访问；也可单独用 VSCode Live Server 插件预览 |
| `wechat-miniprogram/` | 微信小程序 | 需安装「微信开发者工具」并导入此目录 |
| `desktop-tauri/` | Tauri 桌面端 | 需安装 Rust + Cargo + Node.js，详见 `desktop-tauri/README.md` |

**核心运行只需后端**，前端已经挂载在 `/web` 路径下自动提供。

---

## 九、一键流程速查

```
打开 VSCode → 打开文件夹 D:\Desktop\医智中枢
         ↓
  选择 Python 解释器 (Anaconda base, 3.12.7)
         ↓
  按 F5 启动后端 (或终端 uvicorn 命令)
         ↓
  浏览器访问 http://localhost:8000/web/sitemap.html
         ↓
  用演示账号登录体验
```

**完事。项目已经可以直接运行了。**