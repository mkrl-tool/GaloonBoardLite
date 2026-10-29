from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen

class MarkerPocket(QWidget):
    """ホワイトボード右下のマーカー＆イレーザー入れアクセント"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(68, 64)
        self.setToolTip("ガルーン行動予定表")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. 黒マーカー（左側）
        painter.setBrush(QBrush(QColor("#18181b"))) # 黒
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(10, 6, 8, 48, 3, 3)
        # マーカーキャップ
        painter.setBrush(QBrush(QColor("#3f3f46")))
        painter.drawRect(10, 18, 8, 3)

        # 2. 赤マーカー（中央）
        painter.setBrush(QBrush(QColor("#dc2626"))) # 赤
        painter.drawRoundedRect(22, 10, 8, 44, 3, 3)
        # マーカーキャップ
        painter.setBrush(QBrush(QColor("#ef4444")))
        painter.drawRect(22, 22, 8, 3)

        # 3. イレーザー（右側）
        # 青い取っ手部分
        painter.setBrush(QBrush(QColor("#2563eb")))
        painter.drawRoundedRect(36, 16, 26, 38, 4, 4)
        # 白いフェルト部分
        painter.setBrush(QBrush(QColor("#f8fafc")))
        painter.drawRect(37, 36, 24, 16)

        # 4. 透明ポケット（手前のプラスチックケース）
        pocket_color = QColor(226, 232, 240, 180) # 半透明グレー
        border_color = QColor(148, 163, 184, 220)
        painter.setBrush(QBrush(pocket_color))
        painter.setPen(QPen(border_color, 1.5))
        painter.drawRoundedRect(4, 26, 60, 36, 4, 4)
