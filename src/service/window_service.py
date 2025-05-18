import win32gui
import win32con
import win32api
import time
import psutil
import win32process
from src.util.logger import Logger
from pywinauto import Desktop
from pywinauto.clipboard import GetData
from config.key_config import KEY_MAP

class WindowService:
    def __init__(self):
        self.logger = Logger()

    def activate_window(self, app_path):
        """
        激活指定应用程序窗口
        :param app_path: 应用程序完整路径
        :return: 成功返回窗口句柄，失败抛出异常
        """
        hwnd_found = None
        
        def callback(hwnd, extra):
            nonlocal hwnd_found
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc = psutil.Process(pid)
                    if proc.exe().lower() == app_path.lower():
                        hwnd_found = hwnd
                        if win32gui.IsIconic(hwnd):
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetForegroundWindow(hwnd)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return True

        win32gui.EnumWindows(callback, None)
        
        if hwnd_found:
            return hwnd_found
        raise Exception("未找到匹配窗口")

    def _process_single_key(self, key: str):
        """
        处理单个按键
        :param key: 单个按键字符串
        """
        if key == '':  # 处理空字符停顿
            time.sleep(0.5)
            return
        
        if len(key) == 1:
            vk = ord(key.upper())
        elif key in KEY_MAP:
            vk = KEY_MAP[key]
        else:
            for char in key:
                vk = ord(char.upper())
                win32api.keybd_event(vk, 0, 0, 0)
                win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.05)
            return
        
        win32api.keybd_event(vk, 0, 0, 0)
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)

    def send_key(self, keys):
        """
        发送组合键（支持格式：'CTRL C' 或单个键，花括号内为组合键）
        :param keys: 组合键字符串（用空格连接）或单个键
        """
        key_sequence = [k.strip().upper() for k in keys.split(' ')]
        print(key_sequence)
        for key in key_sequence:
            if key.startswith('{') and key.endswith('}'):
                combination = key[1:-1]
                self.send_key_combination(combination)
            else:
                self._process_single_key(key)

    def _get_virtual_key_codes(self, key_sequence: list):
        """
        将按键序列转换为虚拟键码
        :param key_sequence: 按键序列
        :return: 虚拟键码列表
        """
        vk_codes = []
        for key in key_sequence:
            if len(key) == 1:
                vk_codes.append(ord(key.upper()))
            elif key in KEY_MAP:
                vk_codes.append(KEY_MAP[key])
            else:
                raise ValueError(f"无效的按键: {key}")
        return vk_codes

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

    def send_key_combination(self, keys: str, delay: float = 0.1):
        """
        发送组合键（支持格式：'CTRL+SHIFT+A'）
        :param keys: 组合键字符串（用+连接）
        :param delay: 按键之间的延迟时间（秒）
        """
        key_sequence = [k.strip().upper() for k in keys.split('+')]
        key_sequence = [k.replace('\\PLUS', '+') for k in key_sequence]
        
        vk_codes = self._get_virtual_key_codes(key_sequence)

        self._press_modifier_keys(vk_codes, delay)
        win32api.keybd_event(vk_codes[-1], 0, 0, 0)
        time.sleep(delay)
        win32api.keybd_event(vk_codes[-1], 0, win32con.KEYEVENTF_KEYUP, 0)
        self._release_modifier_keys(vk_codes, delay)

    def get_target_window(self, window_params):
        """
        根据参数获取目标窗口
        :param window_params: 窗口查找参数（字典）
        :return: 找到的窗口
        """
        dialogs = Desktop(backend='uia').windows(**window_params)
        if not dialogs:
            return None
        self.logger.add_log(f"找到的对话框数量: {len(dialogs)}")
        return dialogs[0]

    def find_element_in_window(self, window, control_id):
        """
        在指定窗口中查找控件元素
        :param window: 目标窗口
        :param control_id: 元素的control_id
        :return: 找到的元素
        """
        descendants = window.descendants()
        for element in descendants:
            if element.control_id() == control_id:
                return element
        return None

    def get_clipboard(self, retries=3, delay=0.1):
        """
        获取剪切板里的数据
        :param retries: 重试次数，默认3次
        :param delay: 每次重试的延迟时间，默认0.1秒
        :return: 剪切板数据
        """
        for i in range(retries):
            try:
                data = GetData()
                if data:
                    return data
            except Exception as e:
                if i == retries - 1:
                    raise Exception(f"获取剪切板数据失败: {str(e)}")
                time.sleep(delay)
        return None

    def click_element(self, window_params, control_id, retries=3, delay=0.5):
        """
        点击元素
        :param window_params: 窗口查找参数
        :param control_id: 元素的control_id
        :param retries: 重试次数，默认3次
        :param delay: 每次重试的延迟时间，默认0.5秒
        """
        for i in range(retries):
            try:
                window = self.get_target_window(window_params)
                if window is None:
                    raise Exception("未找到目标窗口")
                element = self.find_element_in_window(window, control_id)
                if element is None:
                    raise Exception("未找到目标元素")
                element.click_input()
                return
            except Exception as e:
                if i == retries - 1:
                    raise Exception(f"点击元素失败: {str(e)}")
                time.sleep(delay)