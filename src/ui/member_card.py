from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from ..models import MemberStatus, Event, StatusType
from .event_detail_dialog import EventDetailDialog

class MemberCard(QFrame):
    event_clicked = pyqtSignal(Event)

    def __init__(self, status: MemberStatus, parent=None):
        super().__init__(parent)
        self.status = status
        self.is_expanded = False
        self.init_ui()

    def init_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("""
            MemberCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            MemberCard:hover {
                border: 1px solid #cbd5e1;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(6)

        # 1行目: メンバー名 ＆ 現在ステータスバッジ
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        # ユーザーアイコン風円形アバター
        avatar_lbl = QLabel(self.status.user.name[0] if self.status.user.name else "U")
        avatar_lbl.setFixedSize(28, 28)
        avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_lbl.setStyleSheet(f"""
            background-color: {self.status.status_bg_color};
            color: {self.status.status_color};
            font-weight: bold;
            font-size: 13px;
            border-radius: 14px;
        """)
        top_layout.addWidget(avatar_lbl)

        # ユーザー名
        name_lbl = QLabel(self.status.user.name)
        name_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        name_lbl.setFont(name_font)
        name_lbl.setStyleSheet("color: #1e293b;")
        top_layout.addWidget(name_lbl)

        top_layout.addStretch()

        # ステータスバッジ
        badge = QLabel(self.status.current_status)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"""
            background-color: {self.status.status_bg_color};
            color: {self.status.status_color};
            border: 1px solid {self.status.status_color};
            font-size: 11px;
            font-weight: bold;
            padding: 2px 10px;
            border-radius: 12px;
        """)
        top_layout.addWidget(badge)

        main_layout.addLayout(top_layout)

        # 2行目: 現在の行動・予定内容
        if self.status.current_event:
            ev = self.status.current_event
            cur_box = QFrame()
            cur_box.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            cur_box.setStyleSheet("""
                QFrame {
                    background-color: #f8fafc;
                    border-left: 3px solid #0284c7;
                    border-radius: 3px;
                    padding: 2px 6px;
                }
                QFrame:hover {
                    background-color: #f1f5f9;
                }
            """)
            cur_layout = QVBoxLayout(cur_box)
            cur_layout.setContentsMargins(6, 4, 6, 4)
            cur_layout.setSpacing(2)

            # 予定件名と時間
            time_str = ev.time_range_str
            subj_text = f"【現在】{ev.subject}"
            if time_str:
                subj_text += f" ({time_str})"
            cur_subj = QLabel(subj_text)
            cur_subj.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
            cur_subj.setStyleSheet("color: #0f172a;")
            cur_subj.setWordWrap(True)
            cur_layout.addWidget(cur_subj)

            if ev.notes:
                notes_short = ev.notes.split("\n")[0][:40]
                if len(ev.notes) > 40:
                    notes_short += "..."
                cur_note = QLabel(f"📍 {notes_short}")
                cur_note.setStyleSheet("color: #64748b; font-size: 10px;")
                cur_layout.addWidget(cur_note)

            # クリックイベント
            cur_box.mousePressEvent = lambda e, event=ev: self._on_event_clicked(event)
            main_layout.addWidget(cur_box)

        # 3行目: 次の予定（現在予定がない場合、または次がある場合）
        if self.status.next_event:
            next_ev = self.status.next_event
            next_time = next_ev.start_time.strftime("%H:%M") if next_ev.start_time else ""
            next_text = f"次: {next_time}〜 {next_ev.subject}"
            next_lbl = QLabel(next_text)
            next_lbl.setStyleSheet("color: #64748b; font-size: 10px;")
            next_lbl.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            next_lbl.mousePressEvent = lambda e, event=next_ev: self._on_event_clicked(event)
            main_layout.addWidget(next_lbl)
        elif not self.status.current_event and self.status.current_status == StatusType.PRESENT:
            free_lbl = QLabel("本日のこの後の予定はありません（在席中）")
            free_lbl.setStyleSheet("color: #94a3b8; font-size: 10px; font-style: italic;")
            main_layout.addWidget(free_lbl)

        # 当日予定の一覧（アコーディオン式または展開エリア）
        if len(self.status.today_events) > 1 or (len(self.status.today_events) == 1 and not self.status.current_event):
            self.expand_btn = QPushButton(f"本日の予定 ({len(self.status.today_events)}件) ▼")
            self.expand_btn.setFlat(True)
            self.expand_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.expand_btn.setStyleSheet("""
                QPushButton {
                    color: #64748b;
                    font-size: 10px;
                    text-align: left;
                    padding: 2px 0px;
                    border: none;
                }
                QPushButton:hover {
                    color: #0284c7;
                }
            """)
            self.expand_btn.clicked.connect(self.toggle_expand)
            main_layout.addWidget(self.expand_btn)

            # 展開用コンテナ
            self.events_container = QWidget()
            events_layout = QVBoxLayout(self.events_container)
            events_layout.setContentsMargins(4, 2, 4, 2)
            events_layout.setSpacing(4)

            for ev in self.status.today_events:
                ev_btn = QPushButton(f"• {ev.time_range_str} {ev.subject}")
                ev_btn.setFlat(True)
                ev_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                ev_btn.setStyleSheet("""
                    QPushButton {
                        color: #334155;
                        font-size: 10px;
                        text-align: left;
                        padding: 2px 4px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #f1f5f9;
                        color: #0284c7;
                    }
                """)
                ev_btn.clicked.connect(lambda checked, event=ev: self._on_event_clicked(event))
                events_layout.addWidget(ev_btn)

            self.events_container.setVisible(False)
            main_layout.addWidget(self.events_container)

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.events_container.setVisible(self.is_expanded)
        arrow = "▲" if self.is_expanded else "▼"
        self.expand_btn.setText(f"本日の予定 ({len(self.status.today_events)}件) {arrow}")

    def _on_event_clicked(self, event: Event):
        dlg = EventDetailDialog(event, self.window())
        dlg.exec()
