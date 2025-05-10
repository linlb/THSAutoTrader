import tkinter as tk
from src.view.automation_view import AutomationView

class AutomationApp:
    def __init__(self, root):
        self.root = root
        # 初始化视图
        self.view = self._init_view()

    def _init_view(self):
        """初始化视图"""
        view = AutomationView(self.root)
        view.pack(fill=tk.BOTH, expand=True)
        return view

    def start(self):
        """启动应用程序"""
        self.root.title("下单辅助程序")
        self.root.geometry("500x300")
        # 设置窗口icon
        try:
            # 修改路径，假设icon.ico放在static目录下
            icon = tk.PhotoImage(file="static/icon.ico")
            self.root.iconphoto(True, icon)
        except Exception as e:
            print(f"无法加载icon: {e}")
        self.root.mainloop()

    def log(self, message):
        """使用新的Logger类记录日志"""
        self.logger.add_log(message)

        