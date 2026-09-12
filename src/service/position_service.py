import os
import threading
import time
import pytesseract
from PIL import Image
from src.util.logger import Logger
from src.service.window_service import WindowService
from src.models.app_model import AppModel
from src.util.gui_diagnostics import trace_gui_step
from src.util.table_parser import parse_tabular_data

class PositionService:
    # 类级别的OCR初始化标志和锁
    _ocr_warmed_up = False
    _ocr_lock = threading.Lock()

    def __init__(self):
        self.window_service = WindowService()
        self.model = AppModel()
        self.logger = Logger()

        # 设置tesseract路径(快速操作，不耗时)
        self._setup_tesseract_path()

        # 启动后台线程进行OCR预热(不阻塞主线程)
        # 注意：必须在所有初始化完成后再启动线程
        if not PositionService._ocr_warmed_up:
            # 使用lambda确保传递完整初始化后的self
            threading.Thread(target=lambda: self._warmup_ocr(), daemon=True).start()

    def _setup_tesseract_path(self):
        """设置tesseract路径（快速操作）"""
        try:
            tesseract_dir = self.model.get_tesseract_dir()
            pytesseract.pytesseract.tesseract_cmd = os.path.join(tesseract_dir, "tesseract.exe")
            self.logger.add_log(f"Tesseract路径已设置: {pytesseract.pytesseract.tesseract_cmd}")
        except Exception as e:
            self.logger.add_log(f"设置tesseract路径失败: {str(e)}")

    def _warmup_ocr(self):
        """后台预热OCR引擎（耗时操作）"""
        with PositionService._ocr_lock:
            if PositionService._ocr_warmed_up:
                return

            try:
                self.logger.add_log("开始OCR引擎预热...")

                # 创建一个小的测试图片(10x10白色图片)
                test_image = Image.new('RGB', (10, 10), color='white')

                # 执行一次OCR操作进行预热
                pytesseract.image_to_string(test_image, config='--psm 6 digits')

                PositionService._ocr_warmed_up = True
                self.logger.add_log("OCR引擎预热完成")
            except Exception as e:
                self.logger.add_log(f"OCR预热失败: {str(e)}")
                # 打印详细的异常信息用于调试
                import traceback
                self.logger.add_log(f"详细错误: {traceback.format_exc()}")

    def _get_captcha_image_path(self) -> str:
        """获取验证码图片保存路径"""
        # 创建cache目录
        cache_dir = self.model.get_cache_dir()
        os.makedirs(cache_dir, exist_ok=True)
        # 返回图片路径
        return os.path.join(cache_dir, "image.png")

    def _click_button(self, window, control_id: int) -> bool:
        """模拟点击按钮"""
        button_result = self.window_service.find_element_in_window(window, control_id)
        if button_result:
            button_result.click()
            return True
        return False

    def _verify_captcha_input(self, window, control_id=2406) -> bool:
        """监测验证码输入是否成功"""
        # 获取验证码输入框
        input_result = self.window_service.find_element_in_window(window, control_id)
        if input_result:
            # 存在说输入错误
            return False
        return True

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
        # 查找验证码图片元素
        image_result = self.window_service.find_element_in_window(window_result, 2405)
        #image_result如果为none，则直接获取剪切板数据
        if image_result is None:
            # 如果没有验证码弹窗，可以直接获取剪切板数据
            data = self._get_clipboard_data()
            self.logger.add_log(f"剪切板数据1: {data}")
            return data

        # 获取验证码图片路径
        image_path = self._get_captcha_image_path()
        # 保存图片
        image_result.capture_as_image().save(image_path)
        self.logger.add_log(f"验证码图片已保存到: {image_path}")

        # 使用 OCR 识别图片内容
        ocr_text = self._recognize_image_with_ocr(image_path)
        if not ocr_text:
            return False

        # 查找验证码输入框并输入验证码
        try:
            self.window_service.input_text_to_element(window_result, 2404, ocr_text)
        except Exception as e:
            self.logger.add_log(f"输入验证码失败: {str(e)}")
            raise Exception(f"输入验证码失败: {str(e)}")
        
        # 点击确定按钮
        if self._click_button(window_result, 1):
            # 检查验证码是否成功
            if self._verify_captcha_input(window_result):
                # 获取剪切板数据
                data = self._get_clipboard_data()
                self.logger.add_log(f"剪切板数据2: {data}")
                return data
            else:
                self.logger.add_log(f"验证码输入错误")
                # 点击取消按钮
                self._click_button(window_result, 2)
                raise Exception("验证码输入错误")
        return False

    def _clean_digits(self, text: str) -> str:
        """清理字符串，只保留数字
        Args:
            text: 原始字符串
        Returns:
            只包含数字的字符串
        """
        return ''.join(filter(str.isdigit, text))

    def _recognize_image_with_ocr(self, image_path: str) -> str:
        """使用OCR识别图片中的文字"""
        try:
            # 打开图片
            image = Image.open(image_path)
            # 识别图片中的文字，只识别数字
            # tesseract路径已在__init__中设置，无需重复设置
            ocr_text = pytesseract.image_to_string(image, config='--psm 6 digits')
            # 清理字符串，只保留数字
            ocr_text = self._clean_digits(ocr_text)
            self.logger.add_log(f"OCR 识别结果: {ocr_text}")
            return ocr_text
        except Exception as e:
            error_msg = f"OCR 识别失败: {str(e)}"
            self.logger.add_log(error_msg)
            return ""

    def handle_copy_captcha(self, image_element):
        captcha_window = trace_gui_step('验证码/定位父窗口', image_element.parent)
        input_element = trace_gui_step('验证码/查找输入框2404', self.window_service.find_element_in_window, captcha_window, 2404)
        confirm_button = trace_gui_step('验证码/查找确认按钮', self.window_service.find_element_in_window, captcha_window, 1)
        if input_element is None or confirm_button is None:
            raise RuntimeError("无法确认复制验证码弹窗的输入框或确认按钮，已停止操作")

        image_path = trace_gui_step('验证码/准备截图路径', self._get_captcha_image_path)
        captcha_image = trace_gui_step('验证码/截图', image_element.capture_as_image)
        trace_gui_step('验证码/保存截图', captcha_image.save, image_path)
        ocr_text = trace_gui_step('验证码/OCR识别', self._recognize_image_with_ocr, image_path)
        if not ocr_text:
            raise RuntimeError("OCR识别复制验证码失败")

        trace_gui_step('验证码/输入', self.window_service.input_text_to_element, captcha_window, 2404, '^a{BACKSPACE}' + ocr_text)
        time.sleep(0.3)
        trace_gui_step('验证码/点击确认', confirm_button.click)
        if not trace_gui_step('验证码/检查输入结果', self._verify_captcha_input, captcha_window):
            trace_gui_step('验证码/取消错误输入', self._click_button, captcha_window, 2)
            raise RuntimeError("复制验证码输入错误")

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

        # 查找验证码图片元素
        image_result = self.window_service.find_element_in_window(window_result, 2405)

        # 如果没有验证码弹窗，可以直接获取剪切板数据
        if image_result is None:
            data = self._get_clipboard_data()
            self.logger.add_log(f"今日成交数据: {data}")
            return data

        # 获取验证码图片路径
        image_path = self._get_captcha_image_path()
        # 保存图片
        image_result.capture_as_image().save(image_path)
        self.logger.add_log(f"验证码图片已保存到: {image_path}")

        # 使用 OCR 识别图片内容
        ocr_text = self._recognize_image_with_ocr(image_path)
        if not ocr_text:
            raise Exception("OCR识别验证码失败")

        # 查找验证码输入框并输入验证码
        try:
            self.window_service.input_text_to_element(window_result, 2404, ocr_text)
        except Exception as e:
            self.logger.add_log(f"输入验证码失败: {str(e)}")
            raise Exception(f"输入验证码失败: {str(e)}")

        # 点击确定按钮
        if self._click_button(window_result, 1):
            # 检查验证码是否成功
            if self._verify_captcha_input(window_result):
                # 获取剪切板数据
                data = self._get_clipboard_data()
                self.logger.add_log(f"今日成交数据: {data}")
                return data
            else:
                self.logger.add_log("验证码输入错误")
                # 点击取消按钮
                self._click_button(window_result, 2)
                raise Exception("验证码输入错误")

        raise Exception("获取今日成交失败")
