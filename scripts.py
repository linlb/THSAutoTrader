import subprocess
import os

def build():
    icon_path = "icon.ico"
    if not os.path.exists(icon_path):
        raise FileNotFoundError(f"图标文件 {icon_path} 不存在")

    # 构建命令列表
    command = [
        "poetry", "run", "pyinstaller", "--onefile", "--noconsole",
        "--add-data", "static/icon.ico;static",
        "--icon", "static/icon.ico",
        "--name", "下单辅助程序",
        "main.py"
    ]

    # 动态添加html相关目录
    if os.path.exists("html"):
        import shutil
        dist_dir = "dist"
        target_path = os.path.join(dist_dir, "html")
        if not os.path.exists(target_path):  # 检查目标目录是否已存在
            shutil.copytree("html", target_path)

    subprocess.run(command)

    # 拷贝Tesseract-OCR目录到dist目录
    tesseract_dir = "Tesseract-OCR"
    if os.path.exists(tesseract_dir):
        import shutil
        dist_dir = "dist"
        target_path = os.path.join(dist_dir, tesseract_dir)
        if not os.path.exists(target_path):  # 检查目标目录是否已存在
            shutil.copytree(tesseract_dir, target_path)
    else:
        raise FileNotFoundError(f"Tesseract-OCR目录 {tesseract_dir} 不存在") 