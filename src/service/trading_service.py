import os
from src.util.logger import Logger
from src.service.window_service import WindowService
from src.models.app_model import AppModel
from src.service.captcha_service import CaptchaService
from src.util.gui_diagnostics import trace_gui_step
from src.util.table_parser import parse_tabular_data
import time

class TradingService:
    def __init__(self, captcha_service=None):
        self.window_service = WindowService()
        self.model = AppModel()
        self.logger = Logger()
        self.captcha_service = captcha_service if captcha_service is not None else CaptchaService()

    def get_pending_orders(self):
        trading_path = self.model.get_trading_app()
        if not trading_path:
            raise ValueError("未配置交易程序路径")

        trace_gui_step('挂单/激活交易窗口', self.window_service.activate_window, trading_path)
        window = trace_gui_step('挂单/查找交易窗口', self.window_service.get_target_window, {'title': '网上股票交易系统5.0'})
        if window is None:
            raise RuntimeError("未找到交易窗口")

        trace_gui_step('挂单/点击窗口聚焦', window.click_input)
        time.sleep(0.3)
        trace_gui_step('挂单/F3切换页面', self.window_service.send_key, 'F3')
        time.sleep(0.3)
        trace_gui_step('挂单/F5刷新', self.window_service.send_key, 'F5')
        time.sleep(0.3)
        trace_gui_step('挂单/单击1047', self.window_service.click_element, window, 1047)
        trace_gui_step('挂单/清空剪贴板', self.window_service.clear_clipboard)
        trace_gui_step('挂单/发送复制', self.window_service.send_key, '{CTRL+C}')

        deadline = time.monotonic() + 3
        captcha_handled = False
        last_clipboard_error = None
        while time.monotonic() < deadline:
            image_element = None
            if not captcha_handled:
                image_element = trace_gui_step('挂单/查找验证码2405', self.window_service.find_element_in_window, window, 2405)
            if image_element is not None and trace_gui_step('挂单/检查验证码可见性', image_element.is_visible):
                trace_gui_step('挂单/处理验证码', self.captcha_service.handle_copy_captcha, image_element)
                captcha_handled = True
                deadline = time.monotonic() + 3
            try:
                data = trace_gui_step('挂单/读取剪贴板', self.window_service.get_clipboard, retries=1)
            except Exception as error:
                last_clipboard_error = error
                time.sleep(0.1)
                continue
            if isinstance(data, str) and data.strip():
                orders = parse_tabular_data(data, required_headers=('证券代码',))
                self.logger.add_log("已复制当前挂单列表")
                return orders
            time.sleep(0.1)

        error_message = "未获取到挂单列表文本，请检查撤单页面；不能据此判断无挂单"
        if last_clipboard_error is not None:
            error_message += f"；最后一次剪贴板错误: {last_clipboard_error}"
        raise RuntimeError(error_message)

    def cancel_all_orders(self, cancel_type=None):
        """撤销委托
        Args:
            cancel_type (str, optional): 撤单类型
                - 'A' 或 None: 全部撤单 (control_id: 30001)
                - 'X': 撤买 (control_id: 30002)
                - 'C': 撤卖 (control_id: 30003)
        """
        try:
            trading_path = self.model.get_trading_app()
            self.window_service.activate_window(trading_path)

            # 获取目标窗口
            window = self.window_service.get_target_window({'title': '网上股票交易系统5.0'})

            # 点击窗口达到聚焦效果，否则快捷键会失效
            window.click_input()
            time.sleep(0.1)

            # 先刷新数据，确保获取最新委托信息
            self.window_service.send_key('F5')
            time.sleep(0.1)

            # 使用F3快捷键打开委托撤单界面
            self.window_service.send_key('F3')
            self.logger.add_log("已打开委托撤单界面")
            time.sleep(0.1)

            # 根据撤单类型选择对应的control_id
            control_id_map = {
                'A': 30001,  # 全部撤单
                'X': 30002,  # 撤买
                'C': 30003   # 撤卖
            }

            # 默认为全部撤单
            control_id = control_id_map.get(cancel_type, 30001)

            # 点击对应的撤单按钮
            self.window_service.click_element(window, control_id)

            operation_name = {
                30001: "全部撤单",
                30002: "撤买",
                30003: "撤卖"
            }.get(control_id, "撤单")

            self.logger.add_log(f"{operation_name}操作完成")
            return True

        except Exception as e:
            error_msg = f"撤单操作失败: {str(e)}"
            self.logger.add_log(error_msg)
            raise Exception(error_msg)
