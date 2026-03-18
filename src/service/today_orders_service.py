import time

from src.models.app_model import AppModel
from src.service.position_service import PositionService
from src.service.window_service import WindowService
from src.util.logger import Logger


class TodayOrdersService:
    """当日委托查询服务"""

    def __init__(self):
        self.model = AppModel()
        self.window_service = WindowService()
        self.logger = Logger()
        # 复用现有验证码 OCR / 剪贴板解析逻辑
        self.position_service = PositionService()

    def get_today_orders(self):
        """获取当日委托数据"""
        try:
            trading_path = self.model.get_trading_app()
            self.window_service.activate_window(trading_path)
        except Exception as e:
            self.logger.add_log(f"激活窗口失败，请检查下单程序是否已启动并且不要进入精简模式: {str(e)}")
            raise Exception(f"激活窗口失败，请检查下单程序是否已启动并且不要进入精简模式: {str(e)}")

        # 使用 title_re 做稳健匹配，避免标题编码差异导致找不到窗口
        window_result = self.window_service.get_target_window({"title_re": ".*交易系统5\\.0.*"})
        if window_result is None:
            raise Exception("未找到交易窗口")

        # 聚焦主窗体，确保快捷键生效
        window_result.click_input()
        time.sleep(0.3)

        # 进入查询菜单
        self.window_service.send_key("F4")
        time.sleep(0.1)

        # 路径: 查询[F4] -> 当日委托
        today_orders_button = self.window_service.find_element_by_tree_path(
            window_result,
            200,
            ["查询[F4]", "当日委托"],
        )
        if today_orders_button is None:
            raise Exception("未找到'当日委托'按钮")

        today_orders_button.click_input()
        self.logger.add_log("已点击'当日委托'按钮")
        time.sleep(0.3)

        # 刷新并复制表格
        self.window_service.send_key("F5")
        time.sleep(0.1)
        self.window_service.click_element(window_result, 1047)
        self.window_service.send_key("{CTRL+C}")

        # 处理可能出现的验证码弹窗（复用 position_service 逻辑）
        image_result = self.window_service.find_element_in_window(window_result, 2405)
        if image_result is None:
            data = self.position_service._get_clipboard_data()
            self.logger.add_log(f"当日委托数据: {data}")
            return data

        image_path = self.position_service._get_captcha_image_path()
        image_result.capture_as_image().save(image_path)
        self.logger.add_log(f"验证码图片已保存到: {image_path}")

        ocr_text = self.position_service._recognize_image_with_ocr(image_path)
        if not ocr_text:
            raise Exception("OCR识别验证码失败")

        self.window_service.input_text_to_element(window_result, 2404, ocr_text)

        if self.position_service._click_button(window_result, 1):
            if self.position_service._verify_captcha_input(window_result):
                data = self.position_service._get_clipboard_data()
                self.logger.add_log(f"当日委托数据: {data}")
                return data

            self.position_service._click_button(window_result, 2)
            raise Exception("验证码输入错误")

        raise Exception("获取当日委托失败")
