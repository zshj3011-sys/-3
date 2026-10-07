# MedMind Nexus 患者端微信小程序

> 对应 PRD §M1 患者端应用 · 原生微信小程序工程

## ✨ 特性

- 原生微信小程序 (无 Taro/uni-app 依赖, 体积最小)
- 完整 6 页面 + tabBar (首页 / AI 预问诊 / 智能分诊 / 报告解读 / 用药 / 我的)
- 真实对接后端 `medmind-backend` FastAPI
- 后端不可达时自动回落 `utils/demo.js` 离线演示数据
- 全局 token 管理 + 401 自动清登录态
- 响应式 rpx 单位 + iPhone X 安全区适配

## 📁 工程结构

```
wechat-miniprogram/
├── app.js · app.json · app.wxss · sitemap.json
├── project.config.json          ← 在微信开发者工具中"导入项目"指向此目录
├── pages/
│   ├── home/      首页 (4 卡片入口 + 今日提醒 + 资讯)
│   ├── triage/    AI 预问诊 (多轮对话 + 摘要 + 紧急预警)
│   ├── depts/     智能分诊 (关键词→科室匹配 + 8 个科室)
│   ├── report/    报告解读 (拍照→OCR→AI 解读)
│   ├── meds/      用药提醒 (今日提醒 + 已坚持天数)
│   └── health/    个人档案 (基本信息+过敏史+就诊记录)
├── utils/
│   ├── api.js     后端 API 客户端 (统一拦截 + 401 处理)
│   └── demo.js    离线 demo 数据
└── assets/
    └── tab/       tabBar 图标共 8 个 (home/ai/med/me × 普通 + 选中态，81×81 PNG)
```

## 🚀 运行步骤

1. 在 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html) 中"导入项目"
2. 项目目录选择 `wechat-miniprogram/`
3. AppID 选"测试号"或填入自己的 wxAppID (修改 `project.config.json` 中 `appid`)
4. 修改 `app.js` 中 `baseUrl` 为后端真实地址:
   - 本地调试: `http://localhost:8000`
   - 生产环境: `https://api.your-hospital.com`
5. 开发期勾选"不校验合法域名", 上线前在小程序后台配置 request 合法域名

## 🔌 后端联调

```bash
cd ../medmind-backend
uvicorn app.main:app --reload
```

## 📦 上传发布

正式发布前需要:
1. 申请微信小程序 AppID (https://mp.weixin.qq.com)
2. 在 `project.config.json` 填入真实 AppID
3. 在小程序后台配置"服务器域名" (request 合法域名)
4. 开发者工具 → 上传 → 提交审核

## 🎨 设计规范

- 主题色: `#0EA5A4` (青绿) + `#2563EB` (蓝)
- 单位: 全部使用 `rpx` (750rpx = 屏幕宽)
- 圆角: 卡片 20rpx, 按钮 100rpx (椭圆)
- 阴影: `box-shadow: 0 4rpx 16rpx rgba(15,23,42,.06)`

## ⚙️ TODO (生产化)

- [ ] 接入微信 `RecorderManager` 实现语音输入 → WS /v1/ws/asr
- [ ] 微信支付 (诊费/挂号)
- [ ] 微信订阅消息 (用药提醒推送)
- [ ] 真实 OCR 服务 (报告解读)
- [ ] 分包加载 (减小主包体积)
