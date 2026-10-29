import base64
import requests
from datetime import datetime, date, time, timedelta
from typing import List, Tuple, Optional, Dict, Any
import urllib3

from .config import AppConfig
from .models import User, Event

# SSL自己署名証明書の警告を抑制（社内サーバー用）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GaroonApiClient:
    def __init__(self, config: AppConfig):
        self.config = config

    def _normalize_api_base_url(self, raw_url: str) -> str:
        """ユーザー入力のURLからGaroon REST APIのベースURLを生成"""
        url = raw_url.strip().rstrip("/")
        if not url:
            return ""

        # すでに /api/v1 で終わっている場合
        if url.endswith("/api/v1"):
            return url
        if url.endswith("/api"):
            return f"{url}/v1"

        # パッケージ版の一般的なパターン
        # 例: http://server/cgi-bin/cbgrn/grn.cgi
        # 例: http://server/scripts/cbgrn/grn.exe
        if "grn.cgi" in url or "grn.exe" in url:
            return f"{url}/api/v1"

        # クラウド版のパターン
        # 例: https://subdomain.cybozu.com
        if ".cybozu.com" in url:
            if not url.endswith("/g"):
                url = f"{url}/g"
            return f"{url}/api/v1"

        # その他：とりあえず末尾に /api/v1 を付加
        return f"{url}/api/v1"

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "GaroonYoteiApp/1.0"
        }

        # ガルーンパスワード認証 (X-Cybozu-Authorization: base64(login:password))
        if self.config.username:
            user_pass = f"{self.config.username}:{self.config.password}"
            encoded = base64.b64encode(user_pass.encode("utf-8")).decode("ascii")
            headers["X-Cybozu-Authorization"] = encoded

        # WebサーバーのBasic認証 (Authorization: Basic base64(user:pass))
        if self.config.use_basic_auth and self.config.basic_username:
            basic_up = f"{self.config.basic_username}:{self.config.basic_password}"
            basic_encoded = base64.b64encode(basic_up.encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {basic_encoded}"

        return headers

    def test_connection(self) -> Tuple[bool, str]:
        """接続テストを行い、(成功可否, メッセージ) を返す"""
        if self.config.mock_mode:
            return True, "モックモードが有効です（テスト接続OK）"

        base_url = self._normalize_api_base_url(self.config.garoon_url)
        if not base_url:
            return False, "ガルーンのURLを入力してください。"

        test_url = f"{base_url}/base/users"
        try:
            resp = requests.get(
                test_url,
                headers=self._get_headers(),
                params={"limit": 1},
                verify=self.config.verify_ssl,
                timeout=10
            )

            if resp.status_code == 200:
                data = resp.json()
                total = len(data.get("users", []))
                return True, f"接続に成功しました！（ステータス: 200 OK）"
            elif resp.status_code == 401:
                return False, "認証に失敗しました (401 Unauthorized)。ログイン名・パスワード、またはBasic認証を確認してください。"
            elif resp.status_code == 403:
                return False, "アクセスが拒否されました (403 Forbidden)。REST APIの利用権限があるか確認してください。"
            elif resp.status_code == 404:
                return False, f"APIエンドポイントが見つかりません (404 Not Found)。URL形式を確認してください。\n接続試行先: {test_url}"
            else:
                return False, f"サーバーからエラーが返されました (HTTP {resp.status_code}):\n{resp.text[:200]}"

        except requests.exceptions.SSLError:
            return False, "SSL証明書の検証エラーが発生しました。設定で「SSL検証をスキップ」を有効にしてお試しください。"
        except requests.exceptions.ConnectionError:
            return False, "サーバーに接続できませんでした。ホスト名やネットワーク（VPN・社内LAN）接続を確認してください。"
        except requests.exceptions.Timeout:
            return False, "接続がタイムアウトしました。サーバーの応答がありません。"
        except Exception as e:
            return False, f"接続エラー: {str(e)}"

    def get_users(self) -> List[User]:
        """ユーザー一覧を取得"""
        if self.config.mock_mode:
            return self._get_mock_users()

        base_url = self._normalize_api_base_url(self.config.garoon_url)
        url = f"{base_url}/base/users"
        try:
            resp = requests.get(
                url,
                headers=self._get_headers(),
                params={"limit": 100},
                verify=self.config.verify_ssl,
                timeout=15
            )
            if resp.status_code != 200:
                print(f"Failed to fetch users: {resp.status_code} - {resp.text}")
                return []

            data = resp.json()
            users = []
            for u in data.get("users", []):
                users.append(User(
                    id=str(u.get("id")),
                    name=u.get("name", "名称未設定"),
                    code=u.get("code", ""),
                    email=u.get("email", "")
                ))
            return users
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []

    def get_user_events_for_date(self, user_id: str, target_date: date) -> List[Event]:
        """指定日のユーザーの予定一覧を取得"""
        if self.config.mock_mode:
            return self._get_mock_events_for_user(user_id, target_date)

        base_url = self._normalize_api_base_url(self.config.garoon_url)
        url = f"{base_url}/schedule/events"

        start_dt = datetime.combine(target_date, time.min)
        end_dt = datetime.combine(target_date, time.max)
        
        # ISO8601形式（ローカルタイムゾーン考慮）
        range_start = start_dt.strftime("%Y-%m-%dT00:00:00+09:00")
        range_end = end_dt.strftime("%Y-%m-%dT23:59:59+09:00")

        params = {
            "rangeStart": range_start,
            "rangeEnd": range_end,
            "targetType": "user",
            "target": user_id,
            "orderBy": "start asc",
            "limit": 100
        }

        try:
            resp = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                verify=self.config.verify_ssl,
                timeout=15
            )
            if resp.status_code != 200:
                print(f"Failed to fetch events for user {user_id}: {resp.status_code} {resp.text}")
                return []

            data = resp.json()
            events = []
            for ev in data.get("events", []):
                events.append(self._parse_garoon_event(ev))
            return events
        except Exception as e:
            print(f"Error fetching events for user {user_id}: {e}")
            return []

    def _parse_garoon_event(self, ev_data: Dict[str, Any]) -> Event:
        """Garoon REST APIの予定JSONをEventオブジェクトに変換"""
        ev_id = str(ev_data.get("id", ""))
        subject = ev_data.get("subject", "(無題)")
        event_menu = ev_data.get("eventMenu", "")
        event_type = ev_data.get("eventType", "REGULAR")
        notes = ev_data.get("notes", "")
        visibility = ev_data.get("visibility", "PUBLIC")
        is_all_day = ev_data.get("isAllDay", False)

        start_time = None
        end_time = None

        start_dict = ev_data.get("start", {})
        end_dict = ev_data.get("end", {})

        if "dateTime" in start_dict:
            start_time = self._parse_iso_datetime(start_dict["dateTime"])
        elif "date" in start_dict:
            d = datetime.strptime(start_dict["date"], "%Y-%m-%d").date()
            start_time = datetime.combine(d, time.min)
            is_all_day = True

        if "dateTime" in end_dict:
            end_time = self._parse_iso_datetime(end_dict["dateTime"])
        elif "date" in end_dict:
            d = datetime.strptime(end_dict["date"], "%Y-%m-%d").date()
            end_time = datetime.combine(d, time.max)
            is_all_day = True

        attendees = []
        for att in ev_data.get("attendees", []):
            if "name" in att:
                attendees.append(att["name"])

        return Event(
            id=ev_id,
            subject=subject,
            event_menu=event_menu,
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            is_all_day=is_all_day,
            notes=notes,
            attendees=attendees,
            visibility=visibility
        )

    def _parse_iso_datetime(self, dt_str: str) -> Optional[datetime]:
        try:
            # Python 3.7+ fromisoformat は ISO 8601 をサポート
            # 末尾のタイムゾーン +09:00 など
            # タイムゾーンを除去してローカルナイーブdatetimeに変換
            if "+" in dt_str:
                dt_str_clean = dt_str.split("+")[0]
            elif "-" in dt_str[10:]:
                # YYYY-MM-DDTHH:MM:SS-05:00
                parts = dt_str[10:].split("-")
                dt_str_clean = dt_str[:10] + parts[0]
            else:
                dt_str_clean = dt_str.rstrip("Z")
            
            return datetime.fromisoformat(dt_str_clean)
        except Exception:
            return None

    # ================= モックデータ生成（デモ用） =================
    def _get_mock_users(self) -> List[User]:
        return [
            User(id="1", name="山田 太郎", code="yamada", email="yamada@example.com"),
            User(id="2", name="佐藤 美咲", code="sato", email="sato@example.com"),
            User(id="3", name="鈴木 一郎", code="suzuki", email="suzuki@example.com"),
            User(id="4", name="高橋 健太", code="takahashi", email="takahashi@example.com"),
            User(id="5", name="伊藤 翔太", code="ito", email="ito@example.com"),
            User(id="6", name="渡辺 裕子", code="watanabe", email="watanabe@example.com"),
        ]

    def _get_mock_events_for_user(self, user_id: str, target_date: date) -> List[Event]:
        # 現在時刻を基準にリアリティのある予定を動的に生成
        now = datetime.now()
        base_d = target_date

        if user_id == "1": # 山田 太郎: 外出・打合せ
            return [
                Event(
                    id="m101",
                    subject="株式会社ABC様 定例打ち合わせ",
                    event_menu="外出",
                    start_time=datetime.combine(base_d, time(10, 0)),
                    end_time=datetime.combine(base_d, time(12, 30)),
                    notes="ABC様 本社ビル3F会議室\n新システム提案資料持参",
                    attendees=["山田 太郎", "佐藤 美咲"]
                ),
                Event(
                    id="m102",
                    subject="営業部 課会",
                    event_menu="会議",
                    start_time=datetime.combine(base_d, time(14, 0)),
                    end_time=datetime.combine(base_d, time(15, 30)),
                    notes="第2会議室",
                    attendees=["山田 太郎", "伊藤 翔太"]
                ),
                Event(
                    id="m103",
                    subject="夕方案件整理・日報",
                    event_menu="",
                    start_time=datetime.combine(base_d, time(17, 0)),
                    end_time=datetime.combine(base_d, time(18, 0)),
                    notes="自席"
                )
            ]
        elif user_id == "2": # 佐藤 美咲: テレワーク・WebMTG
            return [
                Event(
                    id="m201",
                    subject="終日在宅勤務",
                    event_menu="テレワーク",
                    is_all_day=True,
                    notes="連絡はTeamsチャットまたは携帯にお願いします。"
                ),
                Event(
                    id="m202",
                    subject="ABC様 定例打ち合わせ (Web参加)",
                    event_menu="会議",
                    start_time=datetime.combine(base_d, time(10, 0)),
                    end_time=datetime.combine(base_d, time(11, 30)),
                    notes="Teams会議"
                ),
                Event(
                    id="m203",
                    subject="1on1 ミーティング",
                    event_menu="面談",
                    start_time=datetime.combine(base_d, time(16, 0)),
                    end_time=datetime.combine(base_d, time(16, 45)),
                    notes="Zoomにて実施"
                )
            ]
        elif user_id == "3": # 鈴木 一郎: ほぼ在席（集中タイム）
            return [
                Event(
                    id="m301",
                    subject="仕様書作成・設計レビュー準備",
                    event_menu="業務",
                    start_time=datetime.combine(base_d, time(9, 30)),
                    end_time=datetime.combine(base_d, time(12, 0)),
                    notes="自席にて作業"
                ),
                Event(
                    id="m302",
                    subject="開発チーム進捗MTG",
                    event_menu="会議",
                    start_time=datetime.combine(base_d, time(13, 30)),
                    end_time=datetime.combine(base_d, time(14, 30)),
                    notes="オンライン会議"
                )
            ]
        elif user_id == "4": # 高橋 健太: 有給休暇
            return [
                Event(
                    id="m401",
                    subject="有給休暇（私用のため）",
                    event_menu="休暇",
                    is_all_day=True,
                    notes="終日不在です。緊急時はメールにて。"
                )
            ]
        elif user_id == "5": # 伊藤 翔太: 午後外出
            return [
                Event(
                    id="m501",
                    subject="社内研修（セキュリティ教育）",
                    event_menu="研修",
                    start_time=datetime.combine(base_d, time(10, 30)),
                    end_time=datetime.combine(base_d, time(11, 30)),
                    notes="大会議室"
                ),
                Event(
                    id="m502",
                    subject="データセンター機器保守立ち会い（直帰）",
                    event_menu="外出",
                    start_time=datetime.combine(base_d, time(14, 30)),
                    end_time=datetime.combine(base_d, time(18, 0)),
                    notes="品川DC / 完了後そのまま直帰予定"
                )
            ]
        elif user_id == "6": # 渡辺 裕子: 会議と面談
            return [
                Event(
                    id="m601",
                    subject="採用面接（エンジニア候補者）",
                    event_menu="面談",
                    start_time=datetime.combine(base_d, time(11, 0)),
                    end_time=datetime.combine(base_d, time(12, 0)),
                    notes="応接室1"
                ),
                Event(
                    id="m602",
                    subject="全社月次報告会",
                    event_menu="会議",
                    start_time=datetime.combine(base_d, time(15, 0)),
                    end_time=datetime.combine(base_d, time(16, 30)),
                    notes="ホールA / ハイブリッド配信"
                )
            ]
        return []
