import win32gui
import win32con
import win32api
import time
import psutil
import win32process
import ctypes
from src.util.logger import Logger
from pywinauto import Desktop
from pywinauto.keyboard import send_keys
from pywinauto.clipboard import GetData
from config.key_config import KEY_MAP

class WindowService:
    def __init__(self):
        self.logger = Logger()

    def get_window_info(self, hwnd):
        """
        获取窗口详细信息
        :param hwnd: 窗口句柄
        :return: 包含窗口信息的字典
        """
        try:
            # 基础信息
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)

            # 窗口位置和大小
            rect = win32gui.GetWindowRect(hwnd)

            # 进程ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            # 窗口状态
            is_minimized = win32gui.IsIconic(hwnd)
            is_maximized = ctypes.windll.user32.IsZoomed(hwnd)
            is_visible = win32gui.IsWindowVisible(hwnd)

            return {
                "hwnd": hwnd,
                "title": title,
                "class_name": class_name,
                "rect": {
                    "left": rect[0],
                    "top": rect[1],
                    "right": rect[2],
                    "bottom": rect[3],
                    "width": rect[2] - rect[0],
                    "height": rect[3] - rect[1]
                },
                "pid": pid,
                "is_minimized": bool(is_minimized),
                "is_maximized": bool(is_maximized),
                "is_visible": bool(is_visible)
            }
        except Exception as e:
            self.logger.add_log(f"获取窗口信息失败: {str(e)}")
            raise Exception(f"获取窗口信息失败: {str(e)}")

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
                        if not win32gui.IsWindow(hwnd):
                            raise Exception("无效的窗口句柄")
                        if not win32gui.IsWindowVisible(hwnd):
                            raise Exception("窗口不可见或已关闭")
                        try:
                            win32gui.SetForegroundWindow(hwnd)
                        except Exception as e:
                            self.logger.add_log(f"win32gui.SetForegroundWindow 失败，尝试使用 pywinauto.set_focus()，句柄：{hwnd}，错误：{str(e)}")
                            try:
                                from pywinauto import Application
                                app = Application(backend='uia').connect(handle=hwnd)
                                app.window(handle=hwnd).set_focus()
                            except Exception as e2:
                                raise Exception(f"设置前台窗口失败，句柄：{hwnd}，错误1：{str(e)}，错误2：{str(e2)}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return True

        win32gui.EnumWindows(callback, None)
        
        if hwnd_found:
            return hwnd_found
        raise Exception("未找到匹配窗口")

    def activate_window_by_pid(self, pid, retries=3, delay=0.5):
        """
        根据进程ID激活窗口
        :param pid: 目标进程ID
        :param retries: 重试次数，默认3次
        :param delay: 每次重试的延迟时间，默认0.5秒
        :return: 成功返回窗口句柄，失败抛出异常
        """
        hwnd_found = None
        
        def callback(hwnd, extra):
            nonlocal hwnd_found
            if win32gui.IsWindowVisible(hwnd):
                _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                if window_pid == pid:
                    hwnd_found = hwnd
                    if win32gui.IsIconic(hwnd):
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    if not win32gui.IsWindow(hwnd):
                        raise Exception("无效的窗口句柄")
                    if not win32gui.IsWindowVisible(hwnd):
                        raise Exception("窗口不可见或已关闭")
                    try:
                        win32gui.SetForegroundWindow(hwnd)
                    except Exception as e:
                        self.logger.add_log(f"win32gui.SetForegroundWindow 失败，尝试使用 pywinauto.set_focus()，句柄：{hwnd}，错误：{str(e)}")
                        try:
                            from pywinauto import Application
                            app = Application(backend='uia').connect(handle=hwnd)
                            app.window(handle=hwnd).set_focus()
                        except Exception as e2:
                            raise Exception(f"设置前台窗口失败，句柄：{hwnd}，错误1：{str(e)}，错误2：{str(e2)}")
                    return False  # 找到后立即停止枚举
            return True

        for attempt in range(retries):
            win32gui.EnumWindows(callback, None)
            
            if hwnd_found:
                # 验证窗口是否真的激活
                active_hwnd = win32gui.GetForegroundWindow()
                if active_hwnd == hwnd_found:
                    return hwnd_found
                else:
                    # 如果激活失败，尝试再次设置
                    try:
                        win32gui.SetForegroundWindow(hwnd_found)
                    except Exception as e:
                        self.logger.add_log(f"win32gui.SetForegroundWindow 失败，尝试使用 pywinauto.set_focus()，句柄：{hwnd_found}，错误：{str(e)}")
                        try:
                            from pywinauto import Application
                            app = Application(backend='uia').connect(handle=hwnd_found)
                            app.window(handle=hwnd_found).set_focus()
                        except Exception as e2:
                            raise Exception(f"设置前台窗口失败，句柄：{hwnd_found}，错误1：{str(e)}，错误2：{str(e2)}")
                    time.sleep(delay)
            else:
                time.sleep(delay)

        raise Exception(f"未找到匹配窗口，进程ID：{pid}，重试次数：{retries}")

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

    def get_target_window(self, window_params, retries=3, delay=0.5):
        """
        根据参数获取目标窗口
        :param window_params: 窗口查找参数（字典）
        :param retries: 重试次数，默认3次
        :param delay: 每次重试的延迟时间，默认0.5秒
        :return: 找到的窗口
        """
        for i in range(retries):
            try:
                dialogs = Desktop(backend='uia').windows(**window_params)
                if dialogs:
                    self.logger.add_log(f"找到的对话框数量: {len(dialogs)}")
                    return dialogs[0]
                time.sleep(delay)
            except Exception as e:
                if i == retries - 1:
                    raise Exception(f"查找窗口失败: {str(e)}")
                time.sleep(delay)
        return None

    def get_best_match_window(self, window_params, candidate_control_ids, min_match_count=1, retries=3, delay=0.5):
        """
        在多个同类窗口中按控件ID匹配度选择最可能的目标窗口
        """
        candidate_ids = set(candidate_control_ids or [])
        for i in range(retries):
            try:
                dialogs = Desktop(backend='uia').windows(**window_params)
                if not dialogs:
                    time.sleep(delay)
                    continue

                best_dialog = None
                best_score = -1
                for dialog in dialogs:
                    matched_ids = set()
                    for element in dialog.descendants():
                        try:
                            cid = element.control_id()
                            if cid in candidate_ids:
                                matched_ids.add(cid)
                        except Exception:
                            continue

                    score = len(matched_ids)
                    if score > best_score:
                        best_score = score
                        best_dialog = dialog

                if best_dialog is not None and best_score >= min_match_count:
                    self.logger.add_log(f"最佳窗口匹配成功，命中控件数: {best_score}")
                    return best_dialog

                time.sleep(delay)
            except Exception as e:
                if i == retries - 1:
                    raise Exception(f"按控件匹配窗口失败: {str(e)}")
                time.sleep(delay)
        return None

    def find_element_in_window(self, window, control_id):
        """
        在指定窗口中查找控件元素
        :param window: 目标窗口
        :param control_id: 元素的control_id（支持单个id或id列表）
        :return: 找到的元素（单个id返回元素，多个id返回元素列表）
        """
        descendants = window.descendants()
        
        # 如果传入的是单个id，保持原有逻辑
        if isinstance(control_id, (int, str)):
            for element in descendants:
                if element.control_id() == control_id:
                    return element
            return None
        
        # 如果传入的是多个id，批量查找
        elif isinstance(control_id, (list, tuple)):
            result = []
            control_id_set = set(control_id)  # 转换为集合提高查找效率
            for element in descendants:
                if element.control_id() in control_id_set:
                    result.append(element)
                    if len(result) == len(control_id_set):  # 找到所有目标后提前返回
                        break
            return result
        
        raise TypeError("control_id参数类型错误，应为int/str或list/tuple")

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

    def click_element(self, window, control_id, retries=3, delay=0.5):
        """
        点击元素
        :param window: 目标窗口
        :param control_id: 元素的control_id
        :param retries: 重试次数，默认3次
        :param delay: 每次重试的延迟时间，默认0.5秒
        """
        for i in range(retries):
            try:
                element = None
                if isinstance(control_id, (list, tuple)):
                    for cid in control_id:
                        element = self.find_element_in_window(window, cid)
                        if element is not None:
                            break
                else:
                    element = self.find_element_in_window(window, control_id)
                if element is None:
                    raise Exception("未找到目标元素")
                element.click_input()
                return
            except Exception as e:
                if i == retries - 1:
                    raise Exception(f"点击元素失败: {str(e)}")
                time.sleep(delay)

    def input_text_to_element(self, window, control_id, text, delay=0.5, clear_existing=False):
        """
        向指定输入框元素输入文本内容
        :param window: 目标窗口
        :param control_id: 输入框元素的control_id
        :param text: 要输入的文本内容
        :param delay: 操作间隔时间，默认0.5秒
        :return: 成功返回True，失败抛出异常
        """
        try:
            # 查找输入框元素
            input_element = None
            if isinstance(control_id, (list, tuple)):
                for cid in control_id:
                    input_element = self.find_element_in_window(window, cid)
                    if input_element is not None:
                        break
            else:
                input_element = self.find_element_in_window(window, control_id)
            if input_element is None:
                raise Exception(f"未找到control_id为{control_id}的输入框元素")

            # 聚焦输入框
            input_element.set_focus()
            input_element.click_input()
            time.sleep(delay)

            # 输入新内容
            if clear_existing:
                for _ in range(3):
                    try:
                        input_element.set_edit_text("")
                    except Exception:
                        pass
                    try:
                        input_element.type_keys("^a{BACKSPACE}", set_foreground=True)
                    except Exception:
                        pass
                    try:
                        input_element.type_keys("^a{DEL}", set_foreground=True)
                    except Exception:
                        pass
                    try:
                        input_element.type_keys("{HOME}+{END}{BACKSPACE}", set_foreground=True)
                    except Exception:
                        pass
                    try:
                        send_keys("^a{BACKSPACE}", pause=0.01)
                    except Exception:
                        pass

                    time.sleep(0.05)
                    try:
                        current_text = (input_element.window_text() or "").strip()
                    except Exception:
                        current_text = ""
                    if current_text == "":
                        break

                try:
                    input_element.type_keys("^a", set_foreground=True)
                except Exception:
                    try:
                        send_keys("^a", pause=0.01)
                    except Exception:
                        pass

            input_element.type_keys(str(text), with_spaces=True, set_foreground=True)
            self.logger.add_log(f"成功向输入框(control_id:{control_id})输入文本: {text}")
            return True

        except Exception as e:
            error_msg = f"向输入框输入文本失败: {str(e)}"
            self.logger.add_log(error_msg)
            raise Exception(error_msg)

    def find_element_by_tree_path(self, window, root_control_id, path_names):
        """
        在树形结构中按路径查找元素
        :param window: 目标窗口
        :param root_control_id: 根节点的control_id
        :param path_names: 路径名称列表，例如 ["查询[F4]", "当日成交"]
        :return: 找到的元素，未找到返回None
        """
        try:
            # 先找到根节点
            root_element = self.find_element_in_window(window, root_control_id)
            if root_element is None:
                self.logger.add_log(f"未找到根节点，control_id: {root_control_id}")
                return None

            # 从根节点开始逐级查找
            current_element = root_element
            for i, name in enumerate(path_names):
                # 先尝试在直接子元素中查找
                children = current_element.children()
                found = False

                for child in children:
                    try:
                        child_name = child.window_text()
                        if child_name == name:
                            current_element = child
                            found = True
                            self.logger.add_log(f"找到路径节点 [{i+1}/{len(path_names)}]: {name} (直接子元素)")
                            break
                    except Exception as e:
                        # 某些子元素可能无法获取window_text，跳过
                        continue

                # 如果在直接子元素中没找到，尝试在所有后代中查找
                if not found:
                    self.logger.add_log(f"在直接子元素中未找到 {name}，尝试在所有后代中查找...")
                    descendants = current_element.descendants()

                    for descendant in descendants:
                        try:
                            descendant_name = descendant.window_text()
                            if descendant_name == name:
                                current_element = descendant
                                found = True
                                self.logger.add_log(f"找到路径节点 [{i+1}/{len(path_names)}]: {name} (后代元素)")
                                break
                        except Exception as e:
                            continue

                if not found:
                    # 打印调试信息：当前元素的所有子元素名称
                    self.logger.add_log(f"未找到路径节点: {name}")
                    self.logger.add_log("当前元素的所有子元素名称:")
                    for child in children:
                        try:
                            self.logger.add_log(f"  - {child.window_text()}")
                        except:
                            pass
                    return None

            return current_element

        except Exception as e:
            error_msg = f"树形查找失败: {str(e)}"
            self.logger.add_log(error_msg)
            raise Exception(error_msg)
