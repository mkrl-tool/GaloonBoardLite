import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import List

CONFIG_FILENAME = "config.json"

@dataclass
class AppConfig:
    # ガルーン接続設定
    garoon_url: str = "http://garoon.example.local/cgi-bin/cbgrn/grn.cgi"
    username: str = ""
    password: str = ""
    use_basic_auth: bool = False
    basic_username: str = ""
    basic_password: str = ""
    verify_ssl: bool = True
    
    # 動作設定
    refresh_interval_minutes: int = 3
    always_on_top: bool = False
    minimize_to_tray: bool = True
    close_to_tray: bool = True
    notify_on_status_change: bool = False
    window_width: int = 420
    window_height: int = 680
    window_x: int = -1
    window_y: int = -1

    # 監視・表示対象
    target_user_ids: List[str] = field(default_factory=list)
    target_org_id: str = ""
    
    # デモ/モックモード（未設定時やオフライン確認用）
    mock_mode: bool = True

def get_base_dir() -> str:
    """実行ファイルまたはスクリプトのディレクトリを取得"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

get_config_dir = get_base_dir

def get_config_path() -> str:
    """設定ファイルの保存先パスを取得（ポータブル優先）"""
    base_dir = get_base_dir()
    local_config = os.path.join(base_dir, CONFIG_FILENAME)
    return local_config

def load_config() -> AppConfig:
    path = get_config_path()
    if not os.path.exists(path):
        cfg = AppConfig()
        save_config(cfg)
        return cfg
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 未定義の新しいフィールドがあっても安全に読み込めるようフィルタリング
            valid_keys = AppConfig.__annotations__.keys()
            filtered_data = {k: v for k, v in data.items() if k in valid_keys}
            return AppConfig(**filtered_data)
    except Exception as e:
        print(f"Error loading config: {e}")
        return AppConfig()

def save_config(cfg: AppConfig) -> bool:
    try:
        path = get_config_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(cfg), f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
