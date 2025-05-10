from src.util.logger import Logger
from src.models.application_model import ApplicationModel
from src.service.window_service import WindowService
from src.service.flask_service import FlaskApp

import requests

class AutomationController:
    def __init__(self, view):
        self.view = view
        self.model = ApplicationModel()
        self.window_service = WindowService()
        self.logger = Logger()
        self.flask_server = None

    def init_http_server(self):
        """初始化HTTP服务"""
        self.flask_server = FlaskApp(host='localhost', port=5000, controller=self)
        self.flask_server.run_async()
        self.logger.add_log(f"HTTP服务已启动")
        self.logger.add_log(f"健康检查端点：http://{self.flask_server.host}:{self.flask_server.port}/health")
        self.logger.add_log(f"下单接口：http://{self.flask_server.host}:{self.flask_server.port}/send_key?key=600000+ENTER+21+ENTER+++B")

    def handle_activate_window(self):
        """处理窗口激活请求"""
        app_path = self.model.get_target_app()
        result = self.window_service.activate_window(app_path)
        self._handle_result(result, "窗口激活成功", "窗口激活失败")

    def handle_send_key(self):
        """处理按键发送请求"""
        self.handle_activate_window()
        key = self.view.key_entry.get().strip()
        result = self.window_service.send_key(key)
        self._handle_result(result, f"已发送按键 {key}", "按键发送失败")

    def _handle_result(self, result, success_msg, fail_msg):
        """统一处理操作结果"""
        if result.success:
            self.logger.add_log(success_msg)
            if result.data:
                self.logger.add_log(str(result.data))
        else:
            self.logger.add_log(f"{fail_msg}: {result.error}")
