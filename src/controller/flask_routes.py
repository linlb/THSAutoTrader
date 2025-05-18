from flask import request, jsonify
import time
from src.service.window_service import WindowService
from src.models.app_model import AppModel
from src.util.logger import Logger

class FlaskRoutes:
    def __init__(self, controller):
        self.controller = controller
        self.app_model = AppModel()
        self.window_service = WindowService()
        self.logger = Logger.get_instance()

    def health_check(self):
        """健康检查"""
        return jsonify({"status": "healthy", "timestamp": time.time()})

    def click(self):
        result = self.controller.handle_execute_trading()
        if result.success:
            return jsonify({"status": "success", "message": "下单成功"})
        else:
            self.logger.add_log(f"下单失败: {result.error}")
            return jsonify({"status": "error", "message": result.error}), 500

    def send_key(self):
        key = request.args.get('key')
        try:
            self.controller.handle_activate_window()
            time.sleep(0.1)
            self.window_service.send_key(key)
            time.sleep(0.1)
            return jsonify({"status": "success", "message": f"已发送按键 {key}"})
        except Exception as e:
            self.logger.add_log(f"按键发送失败: {str(e)}")
            return jsonify({"status": "error", "message": f"按键发送失败: {str(e)}"})

    def xiadan(self):
        key = request.args.get('key')
        try:
            self.controller.handle_activate_window()
            time.sleep(0.1)
            self.window_service.send_key(key)
            time.sleep(0.1)
            time.sleep(0.5)
            self.window_service.click_element({'class_name': '#32770', 'title':''}, 1006)
            return jsonify({"status": "success", "message": f"已发送按键 {key}"})
        except Exception as e:
            self.logger.add_log(f"按键发送失败: {str(e)}")
            return jsonify({"status": "error", "message": f"按键发送失败: {str(e)}"}) 