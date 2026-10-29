from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import List, Optional
import re

@dataclass
class User:
    id: str
    name: str
    code: str = ""
    email: str = ""

@dataclass
class Event:
    id: str
    subject: str
    event_menu: str = ""
    event_type: str = "REGULAR"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_all_day: bool = False
    notes: str = ""
    location: str = ""
    attendees: List[str] = field(default_factory=list)
    visibility: str = "PUBLIC"

    @property
    def time_range_str(self) -> str:
        if self.is_all_day:
            return "終日"
        if not self.start_time:
            return ""
        s = self.start_time.strftime("%H:%M")
        if self.end_time:
            e = self.end_time.strftime("%H:%M")
            return f"{s} - {e}"
        return f"{s} -"

class StatusType:
    PRESENT = "在席"
    OUT = "外出"
    MEETING = "会議中"
    TELEWORK = "テレワーク"
    VACATION = "休暇"
    BUSY = "予定あり"

@dataclass
class MemberStatus:
    user: User
    current_status: str = StatusType.PRESENT
    current_event: Optional[Event] = None
    next_event: Optional[Event] = None
    today_events: List[Event] = field(default_factory=list)

    @property
    def status_color(self) -> str:
        """ステータスに応じたテーマカラー（HEX）"""
        colors = {
            StatusType.PRESENT: "#22c55e",   # エメラルドグリーン
            StatusType.OUT: "#f97316",       # オレンジ
            StatusType.MEETING: "#3b82f6",   # ブルー
            StatusType.TELEWORK: "#06b6d4",  # シアン
            StatusType.VACATION: "#94a3b8",  # スレートグレー
            StatusType.BUSY: "#a855f7",      # パープル
        }
        return colors.get(self.current_status, "#64748b")

    @property
    def destination_text(self) -> str:
        """ホワイトボード用の『行先』表示文字列"""
        if self.current_event:
            ev = self.current_event
            menu = (ev.event_menu or "").strip()
            subj = (ev.subject or "").strip()
            
            # 直帰
            if "直帰" in subj or "直帰" in menu or "直帰" in ev.notes:
                if menu and menu != subj:
                    return f"{menu} ({subj})"
                return subj or "直帰"

            if menu and subj and menu not in subj:
                return f"{menu} {subj}"
            return subj or menu or "予定あり"

        if self.next_event:
            n_ev = self.next_event
            t_str = n_ev.start_time.strftime("%H:%M") if n_ev.start_time else ""
            n_menu = (n_ev.event_menu or "").strip()
            n_subj = (n_ev.subject or "").strip()
            detail = n_subj if len(n_subj) <= 8 else n_subj[:7] + "…"
            return f"在席 (次 {t_str})"

        return "在席"

    @property
    def return_time_text(self) -> str:
        """ホワイトボード用の『帰社時間』表示文字列"""
        if self.current_event:
            ev = self.current_event
            subj = (ev.subject or "").strip()
            notes = (ev.notes or "").strip()

            if "直帰" in subj or "直帰" in notes:
                return "直帰"
            if ev.is_all_day:
                return "終日"
            if ev.end_time:
                return ev.end_time.strftime("%H:%M")
            return ""

        return "―"

    @property
    def board_ink_color(self) -> str:
        """ホワイトボードマーカーの色（外出: 赤, 会議: 青, 在席: 黒, 休暇: グレー）"""
        if self.current_status == StatusType.OUT:
            return "#dc2626" # 赤マーカー
        elif self.current_status == StatusType.MEETING:
            return "#2563eb" # 青マーカー
        elif self.current_status == StatusType.TELEWORK:
            return "#0284c7" # 水色マーカー
        elif self.current_status == StatusType.VACATION:
            return "#71717a" # グレーマーカー
        return "#18181b" # 黒マーカー

    @property
    def status_bg_color(self) -> str:
        """ステータスバッジの背景カラー（半透明・淡いトーン）"""
        bg_colors = {
            StatusType.PRESENT: "#dcfce7",
            StatusType.OUT: "#ffedd5",
            StatusType.MEETING: "#dbeafe",
            StatusType.TELEWORK: "#cffafe",
            StatusType.VACATION: "#f1f5f9",
            StatusType.BUSY: "#f3e8ff",
        }
        return bg_colors.get(self.current_status, "#f1f5f9")

def determine_status_for_event(event: Event) -> str:
    """予定メニューや件名からステータスを判定"""
    menu = (event.event_menu or "").strip()
    subj = (event.subject or "").strip()
    full_text = f"{menu} {subj}"

    if any(k in full_text for k in ["休暇", "有休", "代休", "休職", "全休", "特休"]):
        return StatusType.VACATION
    if any(k in full_text for k in ["在宅", "テレワーク", "リモート", "WFH"]):
        return StatusType.TELEWORK
    if any(k in full_text for k in ["外出", "出張", "直行", "直帰", "移動", "客先", "訪問", "常駐"]):
        return StatusType.OUT
    if any(k in full_text for k in ["会議", "打合せ", "ミーティング", "面談", "商談", "MTG", "mtg", "1on1", "審査", "レビュー"]):
        return StatusType.MEETING
    
    # メニューが空で一般予定の場合
    if menu == "外出" or menu == "出張":
        return StatusType.OUT
    if menu == "会議" or menu == "打合せ":
        return StatusType.MEETING
    
    return StatusType.BUSY

def calculate_member_status(user: User, events: List[Event], target_dt: datetime) -> MemberStatus:
    """指定時刻におけるユーザーの行動予定ステータスを計算"""
    # 当日のイベントをソート
    def get_sort_key(ev: Event):
        if ev.is_all_day:
            return (0, 0)
        if ev.start_time:
            return (1, ev.start_time.timestamp())
        return (2, 0)

    sorted_events = sorted(events, key=get_sort_key)
    
    current_active_event = None
    next_upcoming_event = None
    active_status = StatusType.PRESENT

    # まず終日予定のチェック（休暇など）
    all_day_status = None
    for ev in sorted_events:
        if ev.is_all_day:
            st = determine_status_for_event(ev)
            if st in [StatusType.VACATION, StatusType.TELEWORK, StatusType.OUT]:
                all_day_status = st
                current_active_event = ev

    # 通常時間指定予定のチェック
    for ev in sorted_events:
        if ev.is_all_day:
            continue
        if ev.start_time and ev.end_time:
            if ev.start_time <= target_dt <= ev.end_time:
                current_active_event = ev
                active_status = determine_status_for_event(ev)
                break
            elif ev.start_time > target_dt:
                if next_upcoming_event is None or ev.start_time < next_upcoming_event.start_time:
                    next_upcoming_event = ev
        elif ev.start_time and ev.start_time <= target_dt:
            # 終了未定または開始のみ
            pass

    if current_active_event:
        if not (all_day_status and current_active_event.is_all_day):
            active_status = determine_status_for_event(current_active_event)
        else:
            active_status = all_day_status
    elif all_day_status:
        active_status = all_day_status

    return MemberStatus(
        user=user,
        current_status=active_status,
        current_event=current_active_event,
        next_event=next_upcoming_event,
        today_events=sorted_events
    )
