import random
from time import sleep

from pywinauto import Application, Desktop

WINDOW_KEYWORD = "网上股票交易系统"


def find_window_handle(keyword=WINDOW_KEYWORD):
    for backend in ("uia", "win32"):
        for win in Desktop(backend=backend).windows():
            title = (win.window_text() or "").strip()
            if keyword in title:
                return backend, win.handle, title
    return None, None, None


backend, hwnd, title = find_window_handle(WINDOW_KEYWORD)
if hwnd is None:
    raise RuntimeError(
        "未找到目标窗口。请确认客户端已打开，未处于精简模式，且脚本与客户端权限一致。"
    )

print(f"命中窗口: backend={backend}, hwnd={hwnd}, title={title}")
app = Application(backend=backend).connect(handle=hwnd)
win = app.window(handle=hwnd)
win.set_focus()

print("==========打印所有的control_id=================")

win.print_control_identifiers()

print("==========打印所有的control_id=================")
