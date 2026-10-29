import os
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal

class AppTrayIcon(QSystemTrayIcon):
    request_show = pyqtSignal()
    request_refresh = pyqtSignal()
    request_settings = pyqtSignal()
    request_quit = pyqtSignal()

    def __init__(self, icon_path: str, parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self.init_icon()
        self.init_menu()

    def init_icon(self):
        if os.path.exists(self.icon_path):
            self.setIcon(QIcon(self.icon_path))
        self.setToolTip("ガルーン行動予定表")
        self.activated.connect(self._on_activated)

    def init_menu(self):
        menu = QMenu()

        show_act = QAction("行動予定表を表示", self)
        show_act.triggered.connect(self.request_show.emit)
        menu.addAction(show_act)

        refresh_act = QAction("今すぐ最新に更新", self)
        refresh_act.triggered.connect(self.request_refresh.emit)
        menu.addAction(refresh_act)

        settings_act = QAction("設定...", self)
        settings_act.triggered.connect(self.request_settings.emit)
        menu.addAction(settings_act)

        menu.addSeparator()

        quit_act = QAction("終了", self)
        quit_act.triggered.connect(self.request_quit.emit)
        menu.addAction(quit_act)

        self.setContextMenu(menu)

    def _on_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.request_show.emit()

    def notify(self, title: str, message: str):
        self.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
