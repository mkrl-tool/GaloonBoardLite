use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: String,
    pub name: String,
    pub code: Option<String>,
    pub email: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    pub id: String,
    pub subject: String,
    pub event_menu: Option<String>,
    pub start_time_str: Option<String>,
    pub end_time_str: Option<String>,
    pub time_range_str: Option<String>,
    pub is_all_day: bool,
    pub notes: Option<String>,
    pub attendees: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemberStatus {
    pub user: User,
    pub current_status: String,
    pub destination_text: String,
    pub return_time_text: String,
    pub board_ink_color: String,
    pub current_event: Option<Event>,
    pub today_events: Vec<Event>,
}

impl MemberStatus {
    pub fn new(user: User, events: Vec<Event>, current_time_str: &str) -> Self {
        let mut active_event: Option<Event> = None;
        let mut next_event: Option<Event> = None;

        for ev in &events {
            if ev.is_all_day {
                if active_event.is_none() {
                    active_event = Some(ev.clone());
                }
                continue;
            }

            if let (Some(ref s), Some(ref e)) = (&ev.start_time_str, &ev.end_time_str) {
                if s.as_str() <= current_time_str && current_time_str <= e.as_str() {
                    active_event = Some(ev.clone());
                    break;
                } else if s.as_str() > current_time_str {
                    if next_event.is_none() {
                        next_event = Some(ev.clone());
                    }
                }
            }
        }

        let mut status = "在席".to_string();
        let mut dest = "在席".to_string();
        let mut ret = "―".to_string();
        let mut color = "#111827".to_string(); // 黒

        if let Some(ref ev) = active_event {
            let menu = ev.event_menu.clone().unwrap_or_default();
            let subj = ev.subject.clone();
            let notes = ev.notes.clone().unwrap_or_default();
            let full = format!("{} {} {}", menu, subj, notes);

            if full.contains("外出") || full.contains("出張") || full.contains("訪問") || full.contains("直行") || full.contains("直帰") {
                status = "外出".to_string();
                color = "#dc2626".to_string(); // 赤
                if full.contains("直帰") {
                    ret = "直帰".to_string();
                } else if let Some(ref e) = ev.end_time_str {
                    ret = e.clone();
                }
                dest = if !menu.is_empty() && !subj.is_empty() && !subj.contains(&menu) {
                    format!("{} {}", menu, subj)
                } else {
                    subj
                };
            } else if full.contains("在宅") || full.contains("テレワーク") || full.contains("リモート") {
                status = "テレワーク".to_string();
                color = "#0284c7".to_string(); // シアン
                dest = "在宅勤務".to_string();
                ret = "終日".to_string();
            } else if full.contains("休") || full.contains("有給") {
                status = "休暇".to_string();
                color = "#71717a".to_string(); // グレー
                dest = "有給休暇".to_string();
                ret = "終日".to_string();
            } else {
                status = "会議中".to_string();
                color = "#2563eb".to_string(); // 青
                if let Some(ref e) = ev.end_time_str {
                    ret = e.clone();
                }
                dest = if !subj.is_empty() { subj } else { menu };
            }
        } else if let Some(ref n) = next_event {
            if let Some(ref s) = n.start_time_str {
                dest = format!("在席 (次 {})", s);
            }
        }

        MemberStatus {
            user,
            current_status: status,
            destination_text: dest,
            return_time_text: ret,
            board_ink_color: color,
            current_event: active_event,
            today_events: events,
        }
    }
}
