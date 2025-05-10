import win32gui
import win32con
import win32api
import time
import psutil
import win32process
from src.models.application_model import OperationResult
from src.util.logger import Logger
from pywinauto import Desktop
from pywinauto.controls.uia_controls import ListItemWrapper
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
                    # 处理普通按键
                    if key == '':  # 处理空字符停顿
                        time.sleep(0.5)
                        continue
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
                        continue
                    
                    # 发送单个按键
                    win32api.keybd_event(vk, 0, 0, 0)  # 按下
                    win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放
                    time.sleep(0.05)  # 添加短暂延迟确保按键顺序
            
            return OperationResult(True)
        except Exception as e:
            return OperationResult(False, error=f"组合键发送失败：{str(e)}")
   
    def send_command(self, command: str):
        """发送组合命令到活动窗口"""
        try:
            # 实现具体的按键发送逻辑
            # 示例实现（需要根据实际使用的库调整）：
            import pyautogui
            pyautogui.write(command)
            self.logger.add_log(f"已成功发送命令: {command}")
            return OperationResult(True, "命令发送成功")
        except Exception as e:
            error_msg = f"命令发送失败: {str(e)}"
            self.logger.add_log(error_msg)
            return OperationResult(False, error_msg)

    def find_and_click_dialog_button(self, class_name='#32770', control_id=1006):
        """
        查找并点击指定对话框中的按钮
        :param class_name: 对话框类名
        :param control_id: 按钮的control_id
        :return: OperationResult
        """
        try:
            dialogs = Desktop(backend='uia').windows(class_name=class_name)
            if not dialogs:
                return OperationResult(False, error="没有找到任何对话框")
            
            self.logger.add_log(f"找到的对话框数量: {len(dialogs)}")
            
            for dialog in dialogs:
                try:
                    descendants = dialog.descendants()
                    for element in descendants:
                        if element.control_id() == control_id:
                            element.click_input()
                            return OperationResult(True, data=f"成功点击control_id={control_id}的按钮")
                except Exception as e:
                    return OperationResult(False, error=f"查找或点击按钮时出错: {str(e)}")
            
            return OperationResult(False, error=f"未找到control_id={control_id}的按钮")
        except Exception as e:
            return OperationResult(False, error=f"对话框操作失败: {str(e)}")

    def _select_order_in_list(self, order_id) -> OperationResult:
        """
        在订单列表中定位并选择指定订单
        :param order_id: 需要操作的订单ID
        :return: OperationResult
        """
        try:
            # 获取撤单窗口
            dialog = Desktop(backend='uia').window(class_name='#32770')
            if not dialog.exists():
                return OperationResult(False, error="未找到撤单窗口")

            # 在列表控件中查找订单
            list_ctrl = dialog.child_window(class_name="SysListView32")
            for item in list_ctrl.items():
                if isinstance(item, ListItemWrapper):
                    if order_id in item.texts():
                        item.select()
                        return OperationResult(True)
            
            return OperationResult(False, error=f"未找到订单ID: {order_id}")
        except Exception as e:
            return OperationResult(False, error=f"订单选择异常: {str(e)}") 