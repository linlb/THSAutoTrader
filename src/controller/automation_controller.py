from src.util.logger import Logger
from src.models.app_model import AppModel
from src.service.window_service import WindowService
from src.service.position_service import PositionService
from src.service.trading_service import TradingService
import os
class AutomationController:
    def __init__(self):
        self.view = None
        self.model = AppModel()
        self.window_service = WindowService()
        self.position_service = PositionService()
        self.trading_service = TradingService()
        self.logger = Logger()

    def handle_activate_window(self):
        """处理窗口激活请求"""
        try:
            app_path = self.model.get_target_app()
            hwnd = self.window_service.activate_window(app_path)
            self.logger.add_log(f"窗口激活成功，窗口句柄：{hwnd}")
            return hwnd
        except Exception as e:
            self.logger.add_log(f"窗口激活失败: {str(e)}")
            raise e

    def handle_send_key(self, key):
        """处理按键发送请求
        Args:
            key (str): 要发送的按键值
        """
        self.handle_activate_window()
        self.window_service.send_key(key)
        self.logger.add_log(f"已发送按键 {key}")

    def handle_click(self):
        """处理模拟点击请求"""
        try:
            self.window_service.click_element({'class_name': '#32770', 'title':''}, 1006)
            self.logger.add_log(f"成功点击control_id=1006的按钮")
        except Exception as e:
            self.logger.add_log(f"点击按钮失败: {str(e)}")

    def get_position(self):
        """获取持仓信息"""
        self.handle_activate_window()
        return self.position_service.get_position()
    
    def get_balance(self):
        """获取资金余额"""
        self.handle_activate_window()
        return self.position_service.get_balance()
    
    def handle_cancel_order(self, order_id=None):
        """处理撤单请求
        Args:
            order_id (str, optional): 委托单号，如果不提供则撤销当前选中的委托
        """
        try:
            return self.trading_service.cancel_order(order_id)
        except Exception as e:
            self.logger.add_log(f"撤单请求失败: {str(e)}")
            raise e
    
    def handle_cancel_all_orders(self):
        """处理撤销所有委托请求"""
        try:
            return self.trading_service.cancel_all_orders()
        except Exception as e:
            self.logger.add_log(f"批量撤单请求失败: {str(e)}")
            raise e
    
    def get_pending_orders(self):
        """获取当前委托单信息"""
        try:
            return self.trading_service.get_pending_orders()
        except Exception as e:
            self.logger.add_log(f"获取委托单请求失败: {str(e)}")
            raise e
