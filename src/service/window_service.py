import win32gui
import win32con
import win32api
import time
import psutil
import win32process
from src.models.application_model import OperationResult
from src.util.logger import Logger
from pywinauto import Desktop
from pywinauto.clipboard import GetData
from config.key_config import KEY_MAP

class WindowService:
    def __init__(self):
        self.logger = Logger()

    def activate_window(self, app_path) -> OperationResult:
        """
        激活指定应用程序窗口
        :param app_path: 应用程序完整路径
        :return: OperationResult
        """
        try:
            # 使用win32gui方式直接查找窗口
            hwnd_found = None
            
            def callback(hwnd, extra):
                nonlocal hwnd_found
                if win32gui.IsWindowVisible(hwnd):
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        proc = psutil.Process(pid)
                        if proc.exe().lower() == app_path.lower():
                            hwnd_found = hwnd
                            # 处理最小化状态
                            if win32gui.IsIconic(hwnd):
                                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            win32gui.SetForegroundWindow(hwnd)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                return True

            win32gui.EnumWindows(callback, None)
            
            if hwnd_found:
                return OperationResult(True, data=f"窗口激活成功，句柄：{hwnd_found}")
            else:
                return OperationResult(False, error=f"未找到匹配窗口")
            
        except Exception as e:
            return OperationResult(False, error=f"窗口激活失败：{str(e)}")

    def _process_single_key(self, key: str) -> OperationResult:
        """
        处理单个按键
        :param key: 单个按键字符串
        :return: OperationResult
        """
        if key == '':  # 处理空字符停顿
            time.sleep(0.5)
            return OperationResult(True)
        
        if len(key) == 1:
            vk = ord(key.upper())
        elif key in KEY_MAP:
            vk = KEY_MAP[key]
        else:
            # 字符串转为数组，逐个发送
            for char in key:
                vk = ord(char.upper())
                win32api.keybd_event(vk, 0, 0, 0)  # 按下
                win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放
                time.sleep(0.05)
            return OperationResult(True)
        
        # 发送单个按键
        win32api.keybd_event(vk, 0, 0, 0)  # 按下
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放
        time.sleep(0.05)  # 添加短暂延迟确保按键顺序
        return OperationResult(True)

    def send_key(self, keys) -> OperationResult:
        """
        发送组合键（支持格式：'CTRL C' 或单个键，花括号内为组合键）
        :param keys: 组合键字符串（用空格连接）或单个键
        :return: OperationResult
        """
        try:
            # 按空格分隔按键序列
            key_sequence = [k.strip().upper() for k in keys.split(' ')]
            # 按顺序处理每个按键
            for key in key_sequence:
                if key.startswith('{') and key.endswith('}'):
                    # 提取花括号内的组合键
                    combination = key[1:-1]
                    # 调用组合键方法
                    result = self.send_key_combination(combination)
                    if not result.success:
                        return result
                else:
                    result = self._process_single_key(key)
                    if not result.success:
                        return result
            
            return OperationResult(True)
        except Exception as e:
            return OperationResult(False, error=f"组合键发送失败：{str(e)}")
        
    def _get_virtual_key_codes(self, key_sequence: list) -> OperationResult:
        """
        将按键序列转换为虚拟键码
        :param key_sequence: 按键序列
        :return: OperationResult(包含虚拟键码列表)
        """
        vk_codes = []
        for key in key_sequence:
            if len(key) == 1:
                vk_codes.append(ord(key.upper()))
            elif key in KEY_MAP:
                vk_codes.append(KEY_MAP[key])
            else:
                return OperationResult(False, error=f"无效的按键: {key}")
        return OperationResult(True, data=vk_codes)

    def _press_modifier_keys(self, vk_codes: list, delay: float) -> None:
        """
        按下所有修饰键
        :param vk_codes: 虚拟键码列表
        :param delay: 按键之间的延迟时间
        """
        for vk in vk_codes[:-1]:
            win32api.keybd_event(vk, 0, 0, 0)
            time.sleep(delay)

    def _release_modifier_keys(self, vk_codes: list, delay: float) -> None:
        """
        释放所有修饰键
        :param vk_codes: 虚拟键码列表
        :param delay: 按键之间的延迟时间
        """
        for vk in reversed(vk_codes[:-1]):
            win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(delay)

    def send_key_combination(self, keys: str, delay: float = 0.1) -> OperationResult:
        """
        发送组合键（支持格式：'CTRL+SHIFT+A'）
        :param keys: 组合键字符串（用+连接）
        :param delay: 按键之间的延迟时间（秒）
        :return: OperationResult
        """
        try:
            # 拆分组合键（支持大小写混合）
            key_sequence = [k.strip().upper() for k in keys.split('+')]
            # 恢复转义的+
            key_sequence = [k.replace('\\PLUS', '+') for k in key_sequence]
            
            # 转换所有按键到虚拟键码
            vk_result = self._get_virtual_key_codes(key_sequence)
            if not vk_result.success:
                return vk_result
            vk_codes = vk_result.data

            # 按下所有修饰键
            self._press_modifier_keys(vk_codes, delay)
            
            # 按下并释放主键
            win32api.keybd_event(vk_codes[-1], 0, 0, 0)
            time.sleep(delay)
            win32api.keybd_event(vk_codes[-1], 0, win32con.KEYEVENTF_KEYUP, 0)
            
            # 释放所有修饰键
            self._release_modifier_keys(vk_codes, delay)
            
            return OperationResult(True)
        except Exception as e:
            return OperationResult(False, error=f"组合键发送失败：{str(e)}")

    def get_target_window(self, window_params) -> OperationResult:
        """
        根据参数获取目标窗口
        :param window_params: 窗口查找参数（字典）
        :return: OperationResult(包含找到的窗口)
        """
        try:
            dialogs = Desktop(backend='uia').windows(**window_params)
            if not dialogs:
                return OperationResult(False, error="没有找到任何对话框")
            print(dialogs)
            self.logger.add_log(f"找到的对话框数量: {len(dialogs)}")

            for dialog in dialogs:
                print(dialog.process_id(), dialog.window_text())

            return OperationResult(True, data=dialogs[0])
        except Exception as e:
            return OperationResult(False, error=f"获取窗口失败: {str(e)}")

    def find_element_in_window(self, window, control_id) -> OperationResult:
        """
        在指定窗口中查找控件元素
        :param window: 目标窗口
        :param control_id: 元素的control_id
        :return: OperationResult(包含找到的元素)
        """
        try:
            descendants = window.descendants()
            for element in descendants:
                if element.control_id() == control_id:
                    print(element.control_id(), element.window_text()) 
                    return OperationResult(True, data=element)
            return OperationResult(False, error=f"未找到control_id={control_id}的元素")
        except Exception as e:
            return OperationResult(False, error=f"查找元素时出错: {str(e)}")


    def get_clipboard(self, retries=3, delay=0.1) -> OperationResult:
        """
        获取剪切板里的数据
        :param retries: 重试次数，默认3次
        :param delay: 每次重试的延迟时间，默认0.1秒
        :return: OperationResult
        """
        for i in range(retries):
            try:
                # 获取剪切板数据
                data = GetData()
                if data:
                    return OperationResult(True, data=data)
                else:
                    return OperationResult(False, error="剪切板中没有数据")
            except Exception as e:
                if i == retries - 1:  # 最后一次尝试仍然失败
                    return OperationResult(False, error=f"获取剪切板数据失败: {str(e)}")
                time.sleep(delay)  # 等待后重试

    def click_element(self, window_params, control_id) -> OperationResult:
        """
        点击元素
        :param window_params: 窗口查找参数
        :param control_id: 元素的control_id
        :return: OperationResult
        """
        # 先获取目标窗口
        window_result = self.get_target_window(window_params)
        if not window_result.success:
            return window_result
        
        # 在窗口中查找元素
        element_result = self.find_element_in_window(window_result.data, control_id)
        if not element_result.success:
            return element_result
        
        # 执行点击操作
        try:
            element = element_result.data
            element.click_input()
            return OperationResult(True, data="元素点击成功")
        except Exception as e:
            return OperationResult(False, error=f"元素点击失败: {str(e)}")