use crate::config::AppConfig;
use crate::models::{Event, MemberStatus, User};
use base64::Engine;
use reqwest::blocking::Client;
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};

pub struct GaroonClient {
    config: AppConfig,
}

impl GaroonClient {
    pub fn new(config: AppConfig) -> Self {
        GaroonClient { config }
    }

    fn normalize_api_url(&self, raw_url: &str) -> String {
        let u = raw_url.trim().trim_end_matches('/');
        if u.ends_with("/api/v1") {
            return u.to_string();
        }
        if u.contains("grn.cgi") || u.contains("grn.exe") {
            return format!("{}/api/v1", u);
        }
        if u.contains(".cybozu.com") {
            if u.ends_with("/g") {
                return format!("{}/api/v1", u);
            }
            return format!("{}/g/api/v1", u);
        }
        format!("{}/api/v1", u)
    }

    fn build_client(&self) -> Result<Client, String> {
        let mut builder = Client::builder();
        if !self.config.verify_ssl {
            builder = builder.danger_accept_invalid_certs(true);
        }
        builder
            .timeout(std::time::Duration::from_secs(10))
            .build()
            .map_err(|e| e.to_string())
    }

    fn get_headers(&self) -> HeaderMap {
        let mut headers = HeaderMap::new();
        headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));

        if !self.config.username.is_empty() {
            let auth_str = format!("{}:{}", self.config.username, self.config.password);
            let encoded = base64::engine::general_purpose::STANDARD.encode(auth_str);
            if let Ok(val) = HeaderValue::from_str(&encoded) {
                headers.insert("X-Cybozu-Authorization", val);
            }
        }

        if self.config.use_basic_auth && !self.config.basic_username.is_empty() {
            let basic_str = format!("{}:{}", self.config.basic_username, self.config.basic_password);
            let encoded = base64::engine::general_purpose::STANDARD.encode(basic_str);
            if let Ok(val) = HeaderValue::from_str(&format!("Basic {}", encoded)) {
                headers.insert(AUTHORIZATION, val);
            }
        }

        headers
    }

    pub fn test_connection(&self) -> (bool, String) {
        if self.config.mock_mode {
            return (true, "モックモードが有効です（テスト接続OK）".to_string());
        }

        let base_url = self.normalize_api_url(&self.config.garoon_url);
        let test_url = format!("{}/base/users?limit=1", base_url);

        let client = match self.build_client() {
            Ok(c) => c,
            Err(e) => return (false, format!("HTTPクライアント初期化エラー: {}", e)),
        };

        match client.get(&test_url).headers(self.get_headers()).send() {
            Ok(resp) => {
                if resp.status().is_success() {
                    (true, "接続に成功しました！（HTTP 200 OK）".to_string())
                } else if resp.status().as_u16() == 401 {
                    (false, "認証エラー (401)。ログイン名またはパスワードを確認してください。".to_string())
                } else if resp.status().as_u16() == 403 {
                    (false, "アクセス拒否 (403)。APIの利用権限があるか確認してください。".to_string())
                } else {
                    (false, format!("サーバーエラー: {}", resp.status()))
                }
            }
            Err(e) => (false, format!("接続エラー: {}", e)),
        }
    }

    pub fn get_board_data(&self, date_str: &str, current_time_str: &str) -> Vec<MemberStatus> {
        if self.config.mock_mode {
            return self.get_mock_board_data(current_time_str);
        }

        // 実際のGaroon APIから取得
        let users = self.get_users();
        let target_ids: std::collections::HashSet<String> = self.config.target_user_ids.iter().cloned().collect();

        let filtered_users: Vec<User> = if target_ids.is_empty() {
            users
        } else {
            users.into_iter().filter(|u| target_ids.contains(&u.id)).collect()
        };

        let mut statuses = Vec::new();
        for u in filtered_users {
            let events = self.get_events_for_user(&u.id, date_str);
            statuses.push(MemberStatus::new(u, events, current_time_str));
        }

        statuses
    }

    pub fn get_users(&self) -> Vec<User> {
        if self.config.mock_mode {
            return self.get_mock_users();
        }

        let base_url = self.normalize_api_url(&self.config.garoon_url);
        let url = format!("{}/base/users?limit=100", base_url);

        let client = match self.build_client() {
            Ok(c) => c,
            Err(_) => return vec![],
        };

        if let Ok(resp) = client.get(&url).headers(self.get_headers()).send() {
            if let Ok(json) = resp.json::<serde_json::Value>() {
                if let Some(arr) = json.get("users").and_then(|v| v.as_array()) {
                    let mut list = Vec::new();
                    for item in arr {
                        let id = item.get("id").map(|v| v.to_string()).unwrap_or_default();
                        let name = item.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string();
                        let code = item.get("code").and_then(|v| v.as_str()).map(|s| s.to_string());
                        list.push(User { id, name, code, email: None });
                    }
                    return list;
                }
            }
        }
        vec![]
    }

    fn get_events_for_user(&self, user_id: &str, date_str: &str) -> Vec<Event> {
        let base_url = self.normalize_api_url(&self.config.garoon_url);
        let range_start = format!("{}T00:00:00+09:00", date_str);
        let range_end = format!("{}T23:59:59+09:00", date_str);

        let url = format!(
            "{}/schedule/events?rangeStart={}&rangeEnd={}&targetType=user&target={}&limit=100",
            base_url, range_start, range_end, user_id
        );

        let client = match self.build_client() {
            Ok(c) => c,
            Err(_) => return vec![],
        };

        let mut events = Vec::new();
        if let Ok(resp) = client.get(&url).headers(self.get_headers()).send() {
            if let Ok(json) = resp.json::<serde_json::Value>() {
                if let Some(arr) = json.get("events").and_then(|v| v.as_array()) {
                    for item in arr {
                        let id = item.get("id").map(|v| v.to_string()).unwrap_or_default();
                        let subject = item.get("subject").and_then(|v| v.as_str()).unwrap_or("").to_string();
                        let event_menu = item.get("eventMenu").and_then(|v| v.as_str()).map(|s| s.to_string());
                        let notes = item.get("notes").and_then(|v| v.as_str()).map(|s| s.to_string());
                        let is_all_day = item.get("isAllDay").and_then(|v| v.as_bool()).unwrap_or(false);

                        let mut s_time = None;
                        let mut e_time = None;
                        if let Some(start_obj) = item.get("start") {
                            if let Some(dt) = start_obj.get("dateTime").and_then(|v| v.as_str()) {
                                s_time = dt.get(11..16).map(|s| s.to_string());
                            }
                        }
                        if let Some(end_obj) = item.get("end") {
                            if let Some(dt) = end_obj.get("dateTime").and_then(|v| v.as_str()) {
                                e_time = dt.get(11..16).map(|s| s.to_string());
                            }
                        }

                        let time_range = if is_all_day {
                            Some("終日".to_string())
                        } else if let (Some(ref s), Some(ref e)) = (&s_time, &e_time) {
                            Some(format!("{} - {}", s, e))
                        } else {
                            None
                        };

                        events.push(Event {
                            id,
                            subject,
                            event_menu,
                            start_time_str: s_time,
                            end_time_str: e_time,
                            time_range_str: time_range,
                            is_all_day,
                            notes,
                            attendees: vec![],
                        });
                    }
                }
            }
        }
        events
    }

    fn get_mock_users(&self) -> Vec<User> {
        vec![
            User { id: "1".into(), name: "山田 太郎".into(), code: Some("yamada".into()), email: None },
            User { id: "2".into(), name: "佐藤 美咲".into(), code: Some("sato".into()), email: None },
            User { id: "3".into(), name: "鈴木 一郎".into(), code: Some("suzuki".into()), email: None },
            User { id: "4".into(), name: "高橋 健太".into(), code: Some("takahashi".into()), email: None },
            User { id: "5".into(), name: "伊藤 翔太".into(), code: Some("ito".into()), email: None },
            User { id: "6".into(), name: "渡辺 裕子".into(), code: Some("watanabe".into()), email: None },
        ]
    }

    fn get_mock_board_data(&self, current_time: &str) -> Vec<MemberStatus> {
        let users = self.get_mock_users();
        let mut list = Vec::new();

        for u in users {
            let events = match u.id.as_str() {
                "1" => vec![
                    Event {
                        id: "m1".into(),
                        subject: "株式会社ABC様 定例打ち合わせ".into(),
                        event_menu: Some("外出".into()),
                        start_time_str: Some("10:00".into()),
                        end_time_str: Some("17:30".into()),
                        time_range_str: Some("10:00 - 17:30".into()),
                        is_all_day: false,
                        notes: Some("新システム進捗報告".into()),
                        attendees: vec!["山田 太郎".into(), "佐藤 美咲".into()],
                    }
                ],
                "2" => vec![
                    Event {
                        id: "m2".into(),
                        subject: "終日在宅勤務".into(),
                        event_menu: Some("テレワーク".into()),
                        start_time_str: None,
                        end_time_str: None,
                        time_range_str: Some("終日".into()),
                        is_all_day: true,
                        notes: Some("Teamsにて連絡可能".into()),
                        attendees: vec!["佐藤 美咲".into()],
                    }
                ],
                "3" => vec![
                    Event {
                        id: "m3".into(),
                        subject: "開発進捗MTG".into(),
                        event_menu: Some("会議".into()),
                        start_time_str: Some("14:00".into()),
                        end_time_str: Some("15:00".into()),
                        time_range_str: Some("14:00 - 15:00".into()),
                        is_all_day: false,
                        notes: Some("自席にて".into()),
                        attendees: vec!["鈴木 一郎".into()],
                    }
                ],
                "4" => vec![
                    Event {
                        id: "m4".into(),
                        subject: "有給休暇".into(),
                        event_menu: Some("休暇".into()),
                        start_time_str: None,
                        end_time_str: None,
                        time_range_str: Some("終日".into()),
                        is_all_day: true,
                        notes: Some("私用のため終日不在".into()),
                        attendees: vec!["高橋 健太".into()],
                    }
                ],
                "5" => vec![
                    Event {
                        id: "m5".into(),
                        subject: "品川DC機器保守立ち会い (直帰)".into(),
                        event_menu: Some("外出".into()),
                        start_time_str: Some("14:30".into()),
                        end_time_str: Some("18:00".into()),
                        time_range_str: Some("14:30 - 18:00".into()),
                        is_all_day: false,
                        notes: Some("完了後そのまま直帰".into()),
                        attendees: vec!["伊藤 翔太".into()],
                    }
                ],
                "6" => vec![
                    Event {
                        id: "m6".into(),
                        subject: "採用面接（エンジニア）".into(),
                        event_menu: Some("面談".into()),
                        start_time_str: Some("11:00".into()),
                        end_time_str: Some("12:00".into()),
                        time_range_str: Some("11:00 - 12:00".into()),
                        is_all_day: false,
                        notes: Some("応接室1".into()),
                        attendees: vec!["渡辺 裕子".into()],
                    }
                ],
                _ => vec![],
            };

            list.push(MemberStatus::new(u, events, current_time));
        }

        list
    }
}
