import time
from src.util.logger import Logger
from src.service.window_service import WindowService
from src.service.captcha_service import CaptchaService
from src.models.app_model import AppModel
from src.util.table_parser import parse_tabular_data

class PositionService:
    def __init__(self, captcha_service=None):
        self.window_service = WindowService()
        self.model = AppModel()
        self.logger = Logger()
        self.captcha_service = captcha_service if captcha_service is not None else CaptchaService()

    def get_position(self):
        """获取当前持仓"""
        # 先激活程序
        # app_path = self.model.get_target_app()
        # self.window_service.activate_window(app_path)
        try:
            # 再激活交易程序
            trading_path = self.model.get_trading_app()
            self.window_service.activate_window(trading_path)
        except Exception as e:
            self.logger.add_log(f"激活窗口失败，请检查下单程序是否已启动并且不要进入精简模式: {str(e)}")
            raise Exception(f"激活窗口失败，请检查下单程序是否已启动并且不要进入精简模式: {str(e)}")
        
        # 获取目标窗口
        window_result = self.window_service.get_target_window({'title': '网上股票交易系统5.0'})

        if window_result is None:
            raise Exception("未找到交易窗口")

        #点击下窗口(达到聚焦效果，否则快捷键会失效)
        window_result.click_input()

        time.sleep(0.3)

        # 先刷新数据，确保获取最新持仓信息
        self.window_service.send_key('F5')
        time.sleep(0.3)

        # 快捷键操作
        self.window_service.send_key('F4')


        # 点击内容区域
        self.window_service.click_element(window_result, 1047)
        
        self.window_service.send_key('{CTRL+C}')
        image_result = self.window_service.find_element_in_window(window_result, 2405)
        if image_result is not None:
            self.captcha_service.handle_copy_captcha(image_result)
        data = self._get_clipboard_data()
        self.logger.add_log(f"持仓数据: {data}")
        return data

    def _get_clipboard_data(self):
        """获取剪切板数据"""
        data = self.window_service.get_clipboard()
        return parse_tabular_data(data)
    
    def get_balance(self):
        """获取资金余额"""
        # 先激活程序
        # app_path = self.model.get_target_app()
        # self.window_service.activate_window(app_path)
        try:
            # 再激活交易程序
            trading_path = self.model.get_trading_app()
            self.window_service.activate_window(trading_path)
        except Exception as e:
            self.logger.add_log(f"激活窗口失败，请检查下单程序是否已启动并且不要进入精简模式: {str(e)}")
            raise Exception(f"激活窗口失败，请检查下单程序是否已启动并且不要进入精简模式: {str(e)}")

        # 获取目标窗口
        window_result = self.window_service.get_target_window({'title': '网上股票交易系统5.0'})

        if window_result is None:
            raise Exception("未找到交易窗口")

        #点击下窗口(达到聚焦效果，否则快捷键会失效)
        window_result.click_input()
        time.sleep(0.3)

        # 先刷新数据，确保获取最新资金信息
        self.window_service.send_key('F5')
        time.sleep(0.3)

        # 快捷键操作
        self.window_service.send_key('F4')

        # 定义需要获取的字段及其对应的control_id
        balance_fields = {
            '资金余额': 1012,
            '冻结金额': 1013,
            '可用金额': 1016,
            '可取金额': 1017,
            '股票市值': 1014,
            '总资产': 1015,
            '持仓盈亏': 1027,
            '当日盈亏': 1026,
            '当日盈亏比': 1029
        }

        # 批量获取所有control_id对应的元素
        control_ids = list(balance_fields.values())
        elements = self.window_service.find_element_in_window(window_result, control_ids)

        # 构建结果字典
        result = {}
        for field_name, control_id in balance_fields.items():
            # 查找对应control_id的元素
            element = next((e for e in elements if e.control_id() == control_id), None)
            if element:
                result[field_name] = element.window_text()
            else:
                result[field_name] = None
                self.logger.add_log(f"未找到 {field_name} 对应的控件")

        self.logger.add_log(f"资金余额: {result}")
        return result

    def get_today_trades(self):
        """获取当日成交"""
        try:
            # 激活交易程序
            trading_path = self.model.get_trading_app()
            self.window_service.activate_window(trading_path)
        except Exception as e:
            self.logger.add_log(f"激活窗口失败，请检查下单程序是否已启动并且不要进入精简模式: {str(e)}")
            raise Exception(f"激活窗口失败，请检查下单程序是否已启动并且不要进入精简模式: {str(e)}")

        # 获取目标窗口
        window_result = self.window_service.get_target_window({'title': '网上股票交易系统5.0'})

        if window_result is None:
            raise Exception("未找到交易窗口")

        # 点击窗口(达到聚焦效果，否则快捷键会失效)
        window_result.click_input()
        time.sleep(0.3)

        # 快捷键操作进入查询界面
        self.window_service.send_key('F4')
        time.sleep(0.1)

        # 在树形菜单中找到"当日成交"按钮并点击
        # 路径: control_id=200 -> "查询[F4]" -> "当日成交"
        today_trades_button = self.window_service.find_element_by_tree_path(
            window_result,
            200,
            ["查询[F4]", "当日成交"]
        )

        if today_trades_button is None:
            raise Exception("未找到'当日成交'按钮")

        # 点击"当日成交"按钮
        today_trades_button.click_input()
        self.logger.add_log("已点击'当日成交'按钮")
        time.sleep(0.3)
        # 先刷新数据，确保获取最新成交信息
        self.window_service.send_key('F5')
        time.sleep(0.1)

        # 点击内容区域
        self.window_service.click_element(window_result, 1047)

        self.window_service.send_key('{CTRL+C}')

        image_result = self.window_service.find_element_in_window(window_result, 2405)
        if image_result is not None:
            self.captcha_service.handle_copy_captcha(image_result)
        data = self._get_clipboard_data()
        self.logger.add_log(f"今日成交数据: {data}")
        return data
