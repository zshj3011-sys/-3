# MedMind Nexus 医生端 PC 桌面端 (Tauri 打包)

> 对应 PRD §M2 "医生端 PC 桌面端" 需求

## 🎯 设计思路

医生端 Web 已在 `MedMindNexus/doctor/` 中完成 (6 个页面)。PC 桌面端**复用同一套前端**, 通过 [Tauri](https://tauri.app) 打包为原生 Windows/macOS/Linux 应用,优势:

- **体积小**: 单文件 < 10 MB (相比 Electron < 50 MB)
- **性能高**: 系统 WebView2/WKWebView, 内存占用低
- **安全**: Rust 后端 + 严格 IPC 白名单
- **跨平台**: 一份代码三平台
- **离线优势**: 可结合本地缓存,弱网环境也能用

## 📦 工程结构

```
desktop-tauri/
├── README.md
├── package.json           ← Node 依赖 (Tauri CLI)
├── tauri.conf.json        ← Tauri 主配置
├── src-tauri/
│   ├── Cargo.toml         ← Rust 依赖
│   ├── tauri.conf.json    ← 应用图标/打包配置
│   ├── src/main.rs        ← Rust 入口
│   └── icons/             ← 应用图标 (各平台尺寸)
└── dist/                  ← 构建产物 (集成自 ../MedMindNexus/doctor/)
```

## 🚀 打包步骤

### 前置依赖
- Node.js 20+
- Rust 1.75+ (`rustup install stable`)
- 平台工具链:
  - Windows: Microsoft C++ Build Tools
  - macOS: Xcode CLI Tools (`xcode-select --install`)
  - Linux: `webkit2gtk-4.0-dev libssl-dev`

### 命令
```bash
# 1) 安装依赖
npm install
npm install -g @tauri-apps/cli

# 2) 开发模式 (热重载)
npm run tauri dev

# 3) 打包当前平台安装包
npm run tauri build
# 产物:
#   - Windows: src-tauri/target/release/bundle/msi/*.msi
#   - macOS:   src-tauri/target/release/bundle/dmg/*.dmg
#   - Linux:   src-tauri/target/release/bundle/appimage/*.AppImage
```

## 🔌 配置说明

打开 `tauri.conf.json` 修改:
- `build.devPath`: 开发时指向后端 `http://localhost:8000/web/doctor/workbench.html`
- `build.distDir`: 构建时指向 `../MedMindNexus/`
- `tauri.windows[0].title`: 应用窗口标题
- `tauri.bundle.identifier`: 唯一应用 ID (e.g. `com.your-hospital.medmind`)

## 📌 适配现有 Web 端

`MedMindNexus/doctor/` 全部页面已经做了响应式 + 真实 API 调用 (`assets/js/api.js`),Tauri 几乎零改动即可打包。

**唯一改动**: 在 `assets/js/api.js` 中如果检测到 Tauri 环境 (`window.__TAURI__`),将 baseUrl 切换到 `http://localhost:8000` 即可(后端可以本机部署或远程部署)。
