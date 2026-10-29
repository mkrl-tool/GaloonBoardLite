import os
import subprocess
import sys

def build():
    print("=== ガルーン行動予定表 exeビルド開始 ===")

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=GaloonBoard",
        "--noconsole",
        "--onefile",
        "--icon=assets/icon.ico",
        "--add-data=assets;assets",
        "--clean",
        "run.py"
    ]

    print("実行コマンド:", " ".join(cmd))
    res = subprocess.run(cmd)

    if res.returncode == 0:
        exe_path = os.path.abspath(os.path.join("dist", "GaloonBoard.exe"))
        print("\n==========================================")
        print("[SUCCESS] Build completed successfully!")
        print(f"Executable: {exe_path}")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"File size: {size_mb:.2f} MB")
            # 可能な場合は GaloonYotei.exe にもコピー
            try:
                import shutil
                legacy_path = os.path.join("dist", "GaloonYotei.exe")
                shutil.copy2(exe_path, legacy_path)
                print(f"Copied to: {legacy_path}")
            except Exception:
                pass
        print("==========================================\n")
    else:
        print(f"[ERROR] Build failed with code: {res.returncode}")

if __name__ == "__main__":
    build()
