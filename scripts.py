import subprocess
import os

def build():
    icon_path = "icon.ico"
    if not os.path.exists(icon_path):
        raise FileNotFoundError(f"图标文件 {icon_path} 不存在")

    subprocess.run([
        "poetry", "run", "pyinstaller", "--onefile", "--noconsole",
        "--add-data", "static/icon.ico;static",
        "--icon", "static/icon.ico",
        "--name", "下单辅助程序",
        "main.py"
    ]) 