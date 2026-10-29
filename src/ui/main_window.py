import os
import sys
from datetime import datetime, date, timedelta
from typing import List, Dict

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QFont, QCloseEvent

from ..config import AppConfig, save_config
from ..models import User, Event, MemberStatus, calculate_member_status
from ..garoon_api import GaroonApiClient
from ..utils import get_resource_path
from .whiteboard_row import WhiteboardRow
from .marker_pocket import MarkerPocket
from .settings_dialog import SettingsDialog
from .tray_icon import AppTrayIcon

MIN_BOARD_ROWS = 12

class FetchDataWorker(QObject):
    finished = pyqtSignal(list, str) # List[MemberStatus], error_msg

    def __init__(self, config: AppConfig, target_date: date):
        super().__init__()
        self.config = config
        self.target_date = target_date

    def run(self):
        client = GaroonApiClient(self.config)
        try:
            all_users = client.get_users()
            if not all_users:
                self.finished.emit([], "メンバー情報を取得できませんでした。")
                return

            target_ids = set(self.config.target_user_ids)
            if target_ids:
                users = [u for u in all_users if u.id in target_ids]
            else:
                users = all_users

            member_statuses = []
            now_dt = datetime.now()
            if self.target_date == now_dt.date():
                check_dt = now_dt
            else:
                check_dt = datetime.combine(self.target_date, datetime.min.time())

            for u in users:
                events = client.get_user_events_for_date(u.id, self.target_date)
                m_status = calculate_member_status(u, events, check_dt)
                member_statuses.append(m_status)

            self.finished.emit(member_statuses, "")
        except Exception as e:
            self.finished.emit([], f"エラー: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.current_date = date.today()
        self.member_statuses: List[MemberStatus] = []
        self.is_fetching = False

        self.init_window_properties()
        self.init_tray()
        self.init_ui()
        self.init_timer()

        self.refresh_data()

    def init_window_properties(self):
        self.setWindowTitle("行動予定表")
        # 添付画像の縦長ホワイトボードに合わせたサイズ
        w = max(340, min(self.config.window_width, 400))
        h = max(640, min(self.config.window_height, 750))
        self.resize(w, h)

        if self.config.window_x >= 0 and self.config.window_y >= 0:
            self.move(self.config.window_x, self.config.window_y)

        self._update_always_on_top(self.config.always_on_top)

        icon_path = get_resource_path(os.path.join("assets", "icon.ico"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _update_always_on_top(self, enable: bool):
        flags = self.windowFlags()
        if enable:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        if self.isVisible():
            self.show()

    def init_tray(self):
        icon_path = get_resource_path(os.path.join("assets", "icon.ico"))
        self.tray = AppTrayIcon(icon_path, self)
        self.tray.request_show.connect(self.restore_window)
        self.tray.request_refresh.connect(self.refresh_data)
        self.tray.request_settings.connect(self.open_settings)
        self.tray.request_quit.connect(self.quit_app)
        self.tray.show()

    def init_ui(self):
        # ウィンドウ全体背景
        self.setStyleSheet("QMainWindow { background-color: #cbd5e1; }")

        # ホワイトボードの外枠フレーム（アルミ枠風）
        self.board_frame = QFrame()
        self.board_frame.setStyleSheet("""
            QFrame#boardFrame {
                background-color: #ffffff;
                border: 6px solid #64748b;
                border-radius: 18px;
            }
        """)
        self.board_frame.setObjectName("boardFrame")
        self.setCentralWidget(self.board_frame)

        main_layout = QVBoxLayout(self.board_frame)
        main_layout.setContentsMargins(10, 12, 10, 8)
        main_layout.setSpacing(4)

        # 1. 最上部コントロールバー（設定、更新、ピン留め）
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(6, 0, 4, 0)

        # 小さな日付送り
        prev_btn = QPushButton("◀")
        prev_btn.setFixedSize(20, 20)
        prev_btn.setFlat(True)
        prev_btn.setToolTip("前日")
        prev_btn.setStyleSheet("color: #64748b; font-size: 10px; border: none;")
        prev_btn.clicked.connect(self.go_prev_day)
        top_bar.addWidget(prev_btn)

        next_btn = QPushButton("▶")
        next_btn.setFixedSize(20, 20)
        next_btn.setFlat(True)
        next_btn.setToolTip("翌日")
        next_btn.setStyleSheet("color: #64748b; font-size: 10px; border: none;")
        next_btn.clicked.connect(self.go_next_day)
        top_bar.addWidget(next_btn)

        today_btn = QPushButton("今日")
        today_btn.setFlat(True)
        today_btn.setStyleSheet("color: #64748b; font-size: 10px; border: none; padding: 0 4px;")
        today_btn.clicked.connect(self.go_today)
        top_bar.addWidget(today_btn)

        top_bar.addStretch()

        # 最前面ピン留め
        self.pin_btn = QPushButton("📌" if self.config.always_on_top else "📍")
        self.pin_btn.setFixedSize(22, 22)
        self.pin_btn.setCheckable(True)
        self.pin_btn.setChecked(self.config.always_on_top)
        self.pin_btn.setToolTip("最前面にピン留め")
        self.pin_btn.setStyleSheet("border: none; font-size: 11px;")
        self.pin_btn.clicked.connect(self.toggle_always_on_top)
        top_bar.addWidget(self.pin_btn)

        # 更新
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(22, 22)
        self.refresh_btn.setToolTip("最新の予定に更新")
        self.refresh_btn.setStyleSheet("border: none; font-size: 11px;")
        self.refresh_btn.clicked.connect(self.refresh_data)
        top_bar.addWidget(self.refresh_btn)

        # 設定
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(22, 22)
        settings_btn.setToolTip("ガルーン設定")
        settings_btn.setStyleSheet("border: none; font-size: 11px;")
        settings_btn.clicked.connect(self.open_settings)
        top_bar.addWidget(settings_btn)

        main_layout.addLayout(top_bar)

        # 2. ホワイトボード タイトル「行 動 予 定 表」
        title_lbl = QLabel("行 動 予 定 表")
        title_font = QFont("Meiryo", 17, QFont.Weight.Bold)
        title_lbl.setFont(title_font)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("color: #18181b; letter-spacing: 4px; margin-top: 2px;")
        main_layout.addWidget(title_lbl)

        # 3. 日付記入欄（画像にある「______ 日」のスタイル）
        date_bar = QHBoxLayout()
        date_bar.setContentsMargins(14, 0, 14, 4)
        
        self.date_text = QLabel()
        self.date_text.setFont(QFont("Meiryo", 11, QFont.Weight.Bold))
        self.date_text.setStyleSheet("""
            color: #18181b;
            border-bottom: 1.5px solid #18181b;
            padding-bottom: 1px;
            padding-right: 12px;
        """)
        self._update_date_label()
        date_bar.addWidget(self.date_text)
        date_bar.addStretch()

        main_layout.addLayout(date_bar)

        # 4. 列ヘッダー（氏名・行先・帰社時間）
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 6, 12, 4)
        header_layout.setSpacing(10)

        h_name = QLabel("氏名")
        h_name.setFixedWidth(100)
        h_name.setFont(QFont("Meiryo", 11, QFont.Weight.Bold))
        h_name.setStyleSheet("color: #18181b;")
        header_layout.addWidget(h_name)

        h_dest = QLabel("行先")
        h_dest.setFont(QFont("Meiryo", 11, QFont.Weight.Bold))
        h_dest.setStyleSheet("color: #18181b;")
        header_layout.addWidget(h_dest, 1)

        h_time = QLabel("帰社時間")
        h_time.setFixedWidth(70)
        h_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_time.setFont(QFont("Meiryo", 11, QFont.Weight.Bold))
        h_time.setStyleSheet("color: #18181b;")
        header_layout.addWidget(h_time)

        main_layout.addWidget(header_widget)

        # ヘッダー下の仕切り線
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #18181b; margin: 0 10px 2px 10px;")
        main_layout.addWidget(sep)

        # 5. スクロール可能な行リストエリア
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f5f9;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 3px;
            }
        """)

        self.rows_container = QWidget()
        self.rows_container.setStyleSheet("background-color: transparent;")
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(0)
        self.rows_layout.addStretch()

        self.scroll_area.setWidget(self.rows_container)
        main_layout.addWidget(self.scroll_area, 1)

        # 6. 最下部（マーカーポケット ＆ 控えめなステータス）
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(12, 0, 8, 4)

        self.footer_status = QLabel("")
        self.footer_status.setStyleSheet("color: #94a3b8; font-size: 9px;")
        bottom_bar.addWidget(self.footer_status)

        bottom_bar.addStretch()

        # 画像の右下にあるマーカー＆イレーザーポケット
        self.marker_pocket = MarkerPocket()
        bottom_bar.addWidget(self.marker_pocket)

        main_layout.addLayout(bottom_bar)

    def init_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self._update_timer_interval()

    def _update_timer_interval(self):
        if self.config.refresh_interval_minutes > 0:
            ms = self.config.refresh_interval_minutes * 60 * 1000
            self.timer.start(ms)
        else:
            self.timer.stop()

    def _update_date_label(self):
        weekdays = ["月", "火", "水", "木", "金", "土", "日"]
        w = weekdays[self.current_date.weekday()]
        self.date_text.setText(f"{self.current_date.month}月 {self.current_date.day}日 ({w})")

    def go_prev_day(self):
        self.current_date -= timedelta(days=1)
        self._update_date_label()
        self.refresh_data()

    def go_next_day(self):
        self.current_date += timedelta(days=1)
        self._update_date_label()
        self.refresh_data()

    def go_today(self):
        self.current_date = date.today()
        self._update_date_label()
        self.refresh_data()

    def toggle_always_on_top(self):
        self.config.always_on_top = self.pin_btn.isChecked()
        self.pin_btn.setText("📌" if self.config.always_on_top else "📍")
        save_config(self.config)
        self._update_always_on_top(self.config.always_on_top)

    def refresh_data(self):
        if self.is_fetching:
            return

        self.is_fetching = True
        self.refresh_btn.setEnabled(False)
        self.footer_status.setText("更新中...")

        self.thread = QThread()
        self.worker = FetchDataWorker(self.config, self.current_date)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_fetch_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def _on_fetch_finished(self, statuses: List[MemberStatus], error_msg: str):
        self.is_fetching = False
        self.refresh_btn.setEnabled(True)

        if error_msg:
            self.footer_status.setText(error_msg[:25])
            return

        self.member_statuses = statuses
        now_time = datetime.now().strftime("%H:%M")
        mode_str = " (デモ)" if self.config.mock_mode else ""
        self.footer_status.setText(f"更新: {now_time}{mode_str}")
        self.render_rows()

    def render_rows(self):
        """ホワイトボードの行を描画"""
        while self.rows_layout.count() > 1:
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # メンバーの行を追加
        for ms in self.member_statuses:
            row = WhiteboardRow(ms, self)
            self.rows_layout.insertWidget(self.rows_layout.count() - 1, row)

        # ホワイトボードの見た目を再現するため、一定行数まで空欄行で埋める
        blank_rows_needed = max(0, MIN_BOARD_ROWS - len(self.member_statuses))
        for _ in range(blank_rows_needed):
            blank_row = WhiteboardRow(None, self)
            self.rows_layout.insertWidget(self.rows_layout.count() - 1, blank_row)

    def open_settings(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec():
            self._update_timer_interval()
            self._update_always_on_top(self.config.always_on_top)
            self.pin_btn.setChecked(self.config.always_on_top)
            self.pin_btn.setText("📌" if self.config.always_on_top else "📍")
            self.refresh_data()

    def restore_window(self):
        self.showNormal()
        self.activateWindow()

    def closeEvent(self, event: QCloseEvent):
        self.config.window_width = self.width()
        self.config.window_height = self.height()
        self.config.window_x = self.x()
        self.config.window_y = self.y()
        save_config(self.config)

        if self.config.close_to_tray:
            event.ignore()
            self.hide()
            self.tray.notify("行動予定表", "トレイに常駐しています。")
        else:
            event.accept()

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized() and self.config.minimize_to_tray:
                self.hide()
        super().changeEvent(event)

    def quit_app(self):
        self.config.close_to_tray = False
        QApplication.instance().quit()
