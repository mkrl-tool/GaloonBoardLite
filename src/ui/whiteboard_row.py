from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from typing import Optional
from ..models import MemberStatus
from .event_detail_dialog import EventDetailDialog

class WhiteboardRow(QWidget):
    def __init__(self, status: Optional[MemberStatus] = None, parent=None):
        super().__init__(parent)
        self.status = status
        self.init_ui()

    def init_ui(self):
        self.setFixedHeight(38)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor) if self.status else QCursor(Qt.CursorShape.ArrowCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 2, 12, 2)
        layout.setSpacing(10)

        # 1. 氏名欄
        self.name_container = QWidget()
        name_layout = QHBoxLayout(self.name_container)
        name_layout.setContentsMargins(0, 0, 0, 0)
        self.name_label = QLabel()
        name_font = QFont("Meiryo", 11, QFont.Weight.Bold)
        self.name_label.setFont(name_font)
        self.name_label.setStyleSheet("color: #18181b; padding-bottom: 2px;")
        name_layout.addWidget(self.name_label)
        self.name_container.setFixedWidth(100)
        layout.addWidget(self.name_container)

        # 2. 行先欄
        self.dest_container = QWidget()
        dest_layout = QHBoxLayout(self.dest_container)
        dest_layout.setContentsMargins(0, 0, 0, 0)
        self.dest_label = QLabel()
        dest_font = QFont("Meiryo", 10, QFont.Weight.Medium)
        self.dest_label.setFont(dest_font)
        self.dest_label.setStyleSheet("padding-bottom: 2px;")
        dest_layout.addWidget(self.dest_label)
        layout.addWidget(self.dest_container, 1)

        # 3. 帰社時間欄
        self.time_container = QWidget()
        time_layout = QHBoxLayout(self.time_container)
        time_layout.setContentsMargins(0, 0, 0, 0)
        self.time_label = QLabel()
        time_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        self.time_label.setFont(time_font)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("padding-bottom: 2px;")
        time_layout.addWidget(self.time_label)
        self.time_container.setFixedWidth(70)
        layout.addWidget(self.time_container)

        self.update_content()

    def update_content(self):
        if self.status:
            self.name_label.setText(self.status.user.name)
            self.dest_label.setText(self.status.destination_text)
            self.time_label.setText(self.status.return_time_text)

            ink_color = self.status.board_ink_color
            self.dest_label.setStyleSheet(f"color: {ink_color}; font-weight: 500;")
            self.time_label.setStyleSheet(f"color: {ink_color}; font-weight: bold;")

            # ツールチップで本日の全予定を表示
            tooltip_lines = [f"【{self.status.user.name}】 現在: {self.status.current_status}"]
            for ev in self.status.today_events:
                tooltip_lines.append(f"・{ev.time_range_str} {ev.subject}")
            self.setToolTip("\n".join(tooltip_lines))
        else:
            # 空欄行（ホワイトボードの罫線のみ）
            self.name_label.setText("")
            self.dest_label.setText("")
            self.time_label.setText(":")
            self.time_label.setStyleSheet("color: #cbd5e1; font-weight: normal;")
            self.setToolTip("")

    def mousePressEvent(self, event):
        if self.status and (self.status.current_event or self.status.today_events):
            target_ev = self.status.current_event or self.status.today_events[0]
            dlg = EventDetailDialog(target_ev, self.window())
            dlg.exec()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        # ホワイトボードのアンダーラインを描画
        super().paintEvent(event)
        from PyQt6.QtGui import QPainter, QPen, QColor
        painter = QPainter(self)
        pen = QPen(QColor("#71717a"), 1) # 濃いめのグレー罫線
        painter.setPen(pen)

        y = self.height() - 4

        # 氏名アンダーライン
        n_w = self.name_container.width()
        painter.drawLine(12, y, 12 + n_w - 6, y)

        # 行先アンダーライン
        d_x = self.dest_container.x()
        d_w = self.dest_container.width()
        painter.drawLine(d_x, y, d_x + d_w - 6, y)

        # 帰社時間アンダーライン
        t_x = self.time_container.x()
        t_w = self.time_container.width()
        painter.drawLine(t_x, y, t_x + t_w, y)
