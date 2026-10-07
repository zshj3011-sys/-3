// MedMind Nexus 医生工作站 · Tauri 入口
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // 启动时 log
            println!("🩺 MedMind Nexus 医生工作站启动");
            #[cfg(debug_assertions)]
            {
                use tauri::Manager;
                if let Some(window) = app.get_webview_window("main") {
                    window.open_devtools();
                }
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_app_version, health_check])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

/// 暴露给前端 JS 的命令: 获取应用版本
#[tauri::command]
fn get_app_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

/// 暴露给前端 JS 的命令: 本地健康检查 (Rust 端心跳)
#[tauri::command]
fn health_check() -> serde_json::Value {
    serde_json::json!({
        "status": "ok",
        "app": "MedMind Doctor Workstation",
        "version": env!("CARGO_PKG_VERSION"),
        "platform": std::env::consts::OS,
    })
}
