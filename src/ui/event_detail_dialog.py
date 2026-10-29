from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from ..models import Event

class EventDetailDialog(QDialog):
    def __init__(self, event: Event, parent=None):
        super().__init__(parent)
        self.event = event
        self.setWindowTitle("予定の詳細")
        self.setFixedSize(380, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        # 予定メニューバッジ（あれば）
        if self.event.event_menu:
            menu_badge = QLabel(self.event.event_menu)
            menu_badge.setStyleSheet("""
                background-color: #e0f2fe;
                color: #0369a1;
                font-size: 11px;
                font-weight: bold;
                padding: 3px 8px;
                border-radius: 4px;
            """)
            menu_badge.setFixedWidth(menu_badge.sizeHint().width() + 16)
            layout.addWidget(menu_badge)

        # 件名
        title_label = QLabel(self.event.subject)
        title_label.setWordWrap(True)
        title_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1e293b; margin-top: 2px;")
        layout.addWidget(title_label)

        # 区切り線
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #e2e8f0; margin: 4px 0;")
        layout.addWidget(sep)

        # 日時
        time_layout = QHBoxLayout()
        time_icon = QLabel("🕒")
        time_text = QLabel(self.event.time_range_str)
        time_text.setStyleSheet("color: #475569; font-size: 12px; font-weight: 500;")
        time_layout.addWidget(time_icon)
        time_layout.addWidget(time_text)
        time_layout.addStretch()
        layout.addLayout(time_layout)

        # 参加者
        if self.event.attendees:
            att_layout = QHBoxLayout()
            att_icon = QLabel("👥")
            att_text = QLabel(", ".join(self.event.attendees))
            att_text.setWordWrap(True)
            att_text.setStyleSheet("color: #475569; font-size: 11px;")
            att_layout.addWidget(att_icon)
            att_layout.addWidget(att_text)
            att_layout.addStretch()
            layout.addLayout(att_layout)

        # メモ・場所
        notes_label = QLabel("メモ / 場所:")
        notes_label.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600; margin-top: 6px;")
        layout.addWidget(notes_label)

        notes_box = QTextEdit()
        notes_box.setReadOnly(True)
        notes_content = self.event.notes if self.event.notes else "（メモはありません）"
        notes_box.setPlainText(notes_content)
        notes_box.setStyleSheet("""
            QTextEdit {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px;
                color: #334155;
                font-size: 11px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(notes_box)

        # 閉じるボタン
        close_btn = QPushButton("閉じる")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
