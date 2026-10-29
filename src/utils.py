import os
import sys

def get_resource_path(relative_path: str) -> str:
    """PyInstallerの一時解凍ディレクトリ(_MEIPASS)または開発環境のパスを取得"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        # プロジェクトルートディレクトリ
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
