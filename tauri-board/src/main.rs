#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

mod config;
mod garoon;
mod models;

use chrono::Local;
use config::{load_config as cfg_load, save_config as cfg_save, AppConfig};
use garoon::GaroonClient;
use models::{MemberStatus, User};
use std::sync::Mutex;
use tauri::{
    CustomMenuItem, Manager, SystemTray, SystemTrayEvent, SystemTrayMenu, SystemTrayMenuItem, Window,
};

struct AppState {
    config: Mutex<AppConfig>,
}

#[tauri::command]
fn get_board_data(date: String, state: tauri::State<AppState>) -> Vec<MemberStatus> {
    let cfg = state.config.lock().unwrap().clone();
    let client = GaroonClient::new(cfg);
    let now = Local::now().format("%H:%M").to_string();
    client.get_board_data(&date, &now)
}

#[tauri::command]
fn load_config(state: tauri::State<AppState>) -> AppConfig {
    state.config.lock().unwrap().clone()
}

#[tauri::command]
fn save_config(config: AppConfig, state: tauri::State<AppState>) -> bool {
    let ok = cfg_save(&config);
    if ok {
        let mut locked = state.config.lock().unwrap();
        *locked = config;
    }
    ok
}

#[tauri::command]
fn test_connection(config: AppConfig) -> (bool, String) {
    let client = GaroonClient::new(config);
    client.test_connection()
}

#[tauri::command]
fn get_garoon_users(state: tauri::State<AppState>) -> Vec<User> {
    let cfg = state.config.lock().unwrap().clone();
    let client = GaroonClient::new(cfg);
    client.get_users()
}

#[tauri::command]
fn set_always_on_top(always_on_top: bool, window: Window) -> Result<(), String> {
    window.set_always_on_top(always_on_top).map_err(|e| e.to_string())
}

fn main() {
    let initial_config = cfg_load();

    // システムトレイメニュー
    let show_item = CustomMenuItem::new("show".to_string(), "行動予定表を表示");
    let refresh_item = CustomMenuItem::new("refresh".to_string(), "最新に更新");
    let quit_item = CustomMenuItem::new("quit".to_string(), "終了");
    let tray_menu = SystemTrayMenu::new()
        .add_item(show_item)
        .add_item(refresh_item)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(quit_item);

    let system_tray = SystemTray::new().with_menu(tray_menu);

    tauri::Builder::default()
        .manage(AppState {
            config: Mutex::new(initial_config),
        })
        .system_tray(system_tray)
        .on_system_tray_event(|app, event| match event {
            SystemTrayEvent::LeftClick { .. } | SystemTrayEvent::DoubleClick { .. } => {
                if let Some(window) = app.get_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
            SystemTrayEvent::MenuItemClick { id, .. } => match id.as_str() {
                "show" => {
                    if let Some(window) = app.get_window("main") {
                        let _ = window.show();
                        let _ = window.set_focus();
                    }
                }
                "refresh" => {
                    if let Some(window) = app.get_window("main") {
                        let _ = window.eval("if (typeof refreshData === 'function') refreshData();");
                    }
                }
                "quit" => {
                    std::process::exit(0);
                }
                _ => {}
            },
            _ => {}
        })
        .invoke_handler(tauri::generate_handler![
            get_board_data,
            load_config,
            save_config,
            test_connection,
            get_garoon_users,
            set_always_on_top
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
