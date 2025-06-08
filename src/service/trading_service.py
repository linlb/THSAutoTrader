import os
from src.util.logger import Logger
from src.service.window_service import WindowService
from src.models.app_model import AppModel
import time

class TradingService:
    def __init__(self):
        self.window_service = WindowService()
        self.model = AppModel()
        self.logger = Logger()

    def cancel_all_orders(self):
        """撤销所有可撤委托"""
        try:
            trading_path = self.model.get_trading_app()
            self.window_service.activate_window(trading_path)
            # 使用F3快捷键打开委托撤单界面
            self.window_service.send_key('F3')
            self.logger.add_log("已打开委托撤单界面")
            time.sleep(0.1)
            
            self.window_service.click_element({'title': '网上股票交易系统5.0'}, 30001)
            
            self.logger.add_log("批量撤单操作完成")
            return True
            
        except Exception as e:
            error_msg = f"批量撤单操作失败: {str(e)}"
            self.logger.add_log(error_msg)
            raise Exception(error_msg)
