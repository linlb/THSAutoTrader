from src.util.logger import Logger
from src.models.app_model import AppModel
from src.service.window_service import WindowService
class AutomationController:
    def __init__(self, view):
        self.view = view
        self.model = AppModel()
        self.window_service = WindowService()
        self.logger = Logger()

    def handle_activate_window(self):
        """处理窗口激活请求"""
        try:
            app_path = self.model.get_target_app()
            hwnd = self.window_service.activate_window(app_path)
            self.logger.add_log(f"窗口激活成功，窗口句柄：{hwnd}")
        except Exception as e:
            self.logger.add_log(f"窗口激活失败: {str(e)}")

    def handle_send_key(self):
        """处理按键发送请求"""
        try:
            self.handle_activate_window()
            key = self.view.key_entry.get().strip()
            self.window_service.send_key(key)
            self.logger.add_log(f"已发送按键 {key}")
        except Exception as e:
            self.logger.add_log(f"按键发送失败: {str(e)}")

    def handle_click(self):
        """处理模拟点击请求"""
        try:
            self.window_service.click_element({'class_name': '#32770', 'title':''}, 1006)
            self.logger.add_log(f"成功点击control_id=1006的按钮")
        except Exception as e:
            self.logger.add_log(f"点击按钮失败: {str(e)}")
