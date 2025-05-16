import tkinter as tk
from src.view.automation_view import AutomationView
from src.service.flask_service import FlaskApp
from src.util.logger import Logger

class AutomationApp:
    def __init__(self, root):
        self.root = root
        self.logger = Logger()
        # 初始化app视图
        self.view = self._init_view()
        # 初始化http服务
        self.flask_server = self.init_http_server()

    def _init_view(self):
        """初始化app视图"""
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

    def init_http_server(self):
        """初始化HTTP服务"""
        flask_server = FlaskApp(host='localhost', port=5000)
        flask_server.run_async()
        self.log(f"HTTP服务已启动")
        self.log(f"健康检查端点：http://{flask_server.host}:{flask_server.port}/health")
        self.log(f"下单接口：http://{flask_server.host}:{flask_server.port}/xiadan?key=600000+ENTER+21+ENTER")
        return flask_server

    def log(self, message):
        """使用新的Logger类记录日志"""
        self.logger.add_log(message)

        