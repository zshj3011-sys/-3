# 应用图标

本目录已内置 **品牌占位图标**（青色 #0EA5A4 圆角底 + 白色 "M"），
保证 `tauri build` / `tauri dev` **开箱即用、不会因缺图报错**：

- `32x32.png`            — 任务栏 / 小尺寸
- `128x128.png`          — Linux Desktop 标准
- `128x128@2x.png` (256×256) — macOS Retina
- `icon.ico`             — Windows 多尺寸（16/24/32/48/64/128/256）
- `icon.icns`            — macOS 安装包

> 正式上线前建议用客户实际 Logo 替换：

```bash
# 从一张 1024×1024 PNG 自动生成全套
npx @tauri-apps/cli icon ./your-logo.png
```

生成后会自动覆盖本目录所有 5 个文件，无需手动调整。
