import os
from src.util.logger import Logger
from src.service.window_service import WindowService
from src.models.app_model import AppModel

class PositionService:
    def __init__(self):
        self.window_service = WindowService()
        self.model = AppModel()
        self.logger = Logger()

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
        app_path = self.model.get_target_app()
        self.window_service.activate_window(app_path)
        try:
            # 再激活交易程序
            trading_path = self.model.get_trading_app()
            self.window_service.activate_window(trading_path)
        except Exception as e:
            self.logger.add_log(f"激活窗口失败，请检查下单程序是否已启动并且不要进入精简模式: {str(e)}")
            return False
        
        # 获取目标窗口
        window_result = self.window_service.get_target_window({'title': '网上股票交易系统5.0'})

        if window_result is None:
            raise Exception("未找到交易窗口")

        # 快捷键操作
        self.window_service.send_key('F4')
        # 点击内容区域
        self.window_service.click_element({'title': '网上股票交易系统5.0'}, 1047)
        
        self.window_service.send_key('{CTRL+C}')
        # 查找验证码图片元素
        image_result = self.window_service.find_element_in_window(window_result, 2405)
        #image_result如果为none，则直接获取剪切板数据
        print(image_result)
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

        # 查找验证码输入框
        input_result = self.window_service.find_element_in_window(window_result, 2404)
        if input_result:
            # 输入验证码
            input_result.type_keys(ocr_text)
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
                    return False
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
            import pytesseract
            from PIL import Image
            import os
            # 获取程序根目录并设置tesseract路径
            tesseract_dir = self.model.get_tesseract_dir()
            pytesseract.pytesseract.tesseract_cmd = os.path.join(tesseract_dir, "tesseract.exe")
            # 打开图片
            image = Image.open(image_path)
            # 识别图片中的文字，只识别数字
            ocr_text = pytesseract.image_to_string(image, config='--psm 6 digits')
            # 清理字符串，只保留数字
            ocr_text = self._clean_digits(ocr_text)
            self.logger.add_log(f"OCR 识别结果: {ocr_text}")
            return ocr_text
        except Exception as e:
            error_msg = f"OCR 识别失败: {str(e)}"
            self.logger.add_log(error_msg)
            return ""

    def _get_clipboard_data(self):
        """获取剪切板数据"""
        data = self.window_service.get_clipboard()
        return self._format_hold_data(data)

    def _format_hold_data(self, table_data: str) -> list[dict]:
        """将表结构数据转换为JSON格式
        Args:
            table_data: 表结构数据，包含表头和内容
        Returns:
            返回格式化后的JSON数据列表
        """
        # 分割表头和内容
        lines = table_data.splitlines()
        if len(lines) < 2:
            return []
        
        # 获取表头
        headers = lines[0].split('\t')
        # 处理数据行
        result = []
        for line in lines[1:]:
            values = line.split('\t')
            if len(values) != len(headers):
                continue
            # 构建字典
            item = {headers[i]: values[i] for i in range(len(headers))}
            result.append(item)
        
        return result 
    
    def get_balance(self):
        """获取资金余额"""
        # 先激活程序
        app_path = self.model.get_target_app()
        self.window_service.activate_window(app_path)
        try:
            # 再激活交易程序
            trading_path = self.model.get_trading_app()
            self.window_service.activate_window(trading_path)
        except Exception as e:
            self.logger.add_log(f"激活窗口失败，请检查下单程序是否已启动并且不要进入精简模式: {str(e)}")
            return False
        
        # 获取目标窗口
        window_result = self.window_service.get_target_window({'title': '网上股票交易系统5.0'})

        if window_result is None:
            raise Exception("未找到交易窗口")

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