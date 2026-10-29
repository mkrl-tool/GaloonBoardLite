use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

const CONFIG_FILE: &str = "config.json";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub garoon_url: String,
    pub username: String,
    pub password: String,
    pub use_basic_auth: bool,
    pub basic_username: String,
    pub basic_password: String,
    pub verify_ssl: bool,
    pub refresh_interval_minutes: u64,
    pub target_user_ids: Vec<String>,
    pub mock_mode: bool,
}

impl Default for AppConfig {
    fn default() -> Self {
        AppConfig {
            garoon_url: "http://garoon.example.local/cgi-bin/cbgrn/grn.cgi".to_string(),
            username: "".to_string(),
            password: "".to_string(),
            use_basic_auth: false,
            basic_username: "".to_string(),
            basic_password: "".to_string(),
            verify_ssl: true,
            refresh_interval_minutes: 20,
            target_user_ids: vec![],
            mock_mode: true,
        }
    }
}

pub fn get_config_path() -> PathBuf {
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(parent) = exe_path.parent() {
            return parent.join(CONFIG_FILE);
        }
    }
    PathBuf::from(CONFIG_FILE)
}

pub fn load_config() -> AppConfig {
    let path = get_config_path();
    if let Ok(content) = fs::read_to_string(&path) {
        if let Ok(cfg) = serde_json::from_str::<AppConfig>(&content) {
            return cfg;
        }
    }
    let default_cfg = AppConfig::default();
    let _ = save_config(&default_cfg);
    default_cfg
}

pub fn save_config(config: &AppConfig) -> bool {
    let path = get_config_path();
    if let Ok(json) = serde_json::to_string_pretty(config) {
        return fs::write(path, json).is_ok();
    }
    false
}
