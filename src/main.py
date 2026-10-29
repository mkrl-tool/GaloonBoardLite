import sys
import os
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QFont

from src.config import load_config
from src.ui.main_window import MainWindow
from src.utils import get_resource_path

def main():
    # Windowsでタスクバーに個別アプリとしてアイコンを表示させるためのAppUserModelID設定
    try:
        myappid = "cybozu.garoon.scheduleboard.v1"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("ガルーン行動予定表")
    app.setQuitOnLastWindowClosed(False) # トレイ常駐のためウィンドウ閉じても維持

    # アプリ標準フォント
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    # アプリアイコン
    icon_path = get_resource_path(os.path.join("assets", "icon.ico"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 設定読み込み
    config = load_config()

    # メインウィンドウ表示
    window = MainWindow(config)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
