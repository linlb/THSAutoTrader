import random
from time import sleep

from pywinauto import Application, Desktop


WINDOW_KEYWORD = "网上股票交易系统"
# 与 window_service 一致：在整棵子树中按 control_id 查找，不要求是直接子控件
CONTROL_ID_STOCK_CODE = 1032
CONTROL_ID_STOCK_PRICE = 1033
CONTROL_ID_BUY_QUANTITY = 1034
CONTROL_ID_BUY_BUTTON = 1006
PRICE_LIMIT_POPUP_TEXT = "您输入的价格已超出涨跌停限制"


def find_window_handle(keyword=WINDOW_KEYWORD):
    for backend in ("uia", "win32"):
        for win in Desktop(backend=backend).windows():
            title = (win.window_text() or "").strip()
            if keyword in title:
                return backend, win.handle, title
    return None, None, None


def find_element_in_window(window, control_id):
    """在窗口的全体后代中按 control_id 查找控件（与 window_service 一致）。
    用 descendants() 遍历并按 control_id() 匹配，避免 child_window 找不到深层控件导致 spec.wait('ready') 超时。
    """
    for element in window.descendants():
        if element.control_id() == control_id:
            element_name = getattr(element.element_info, "name", "") or ""
            print(f"element的名称为：{element_name}, control_id为：{control_id}")
            return element
    return None


def input_text_to_element(win, control_id, text: str, delay: float = 0.5) -> None:
    """对指定 control_id 的输入框 set_focus 后 type_keys，与 window_service 一致。"""
    element = find_element_in_window(win, control_id)
    if element is None:
        raise RuntimeError(f"未找到 control_id={control_id} 的控件")

    element.click_input()

    sleep(random.uniform(0.2, 0.8))


    for _ in range(10):
        element.type_keys("{RIGHT}", set_foreground=True)
        sleep(random.uniform(0.2, 0.5))
        element.type_keys("{BACKSPACE}", set_foreground=True)

    # for _ in range(10):
    #     element.type_keys("{BACKSPACE}", set_foreground=True)
    #     sleep(random.uniform(0.2, 0.5))

    sleep(random.uniform(0.3, 0.5))
    element.type_keys(text, set_foreground=True, with_spaces=True)


def input_stock_code(win, code: str) -> None:
    code = str(code).strip()
    if not code:
        return
    input_text_to_element(win, CONTROL_ID_STOCK_CODE, code)

def input_stock_price(win, stock_price: str) -> None:
    code = str(stock_price).strip()
    if not code:
        return
    input_text_to_element(win, CONTROL_ID_STOCK_PRICE, stock_price)


def input_buy_quantity(win, quantity) -> None:
    text = str(int(quantity)).strip()
    if not text:
        return
    input_text_to_element(win, CONTROL_ID_BUY_QUANTITY, text)


def goto_buy_page(win) -> None:
    """先发送 F1 跳转到买入页，避免不在下单页时控件查找超时。"""
    win.set_focus()
    sleep(random.uniform(0.2, 0.5))
    win.type_keys("{F1}", set_foreground=True)
    sleep(random.uniform(0.5, 1.0))


def get_buy_button(win):
    """获取买入按钮（由闪电下单控件文件确认 control_id=1006）。"""
    button = find_element_in_window(win, CONTROL_ID_BUY_BUTTON)
    if button is None:
        raise RuntimeError(
            f"未找到买入按钮，期望 control_id={CONTROL_ID_BUY_BUTTON}"
        )
    return button



def _get_dialog_texts(dialog):
    texts = []
    try:
        title = (dialog.window_text() or "").strip()
        if title:
            texts.append(title)
    except Exception:
        pass

    try:
        elements = dialog.descendants()
    except Exception:
        elements = []

    for element in elements:
        try:
            text = (element.window_text() or "").strip()
        except Exception:
            continue
        if text:
            texts.append(text)

    return list(dict.fromkeys(texts))


def _is_price_limit_dialog(dialog, texts):
    title = ""
    try:
        title = (dialog.window_text() or "").strip()
    except Exception:
        pass

    content = " | ".join(texts)
    if "提示信息" not in title and "提示信息" not in content:
        return False

    if PRICE_LIMIT_POPUP_TEXT in content:
        return True

    # 兜底：部分环境文案会带符号或附加区间，只保留这一类提示的强特征
    return ("涨跌停限制" in content) and ("是否继续该笔委托" in content)


def _find_price_limit_dialog(timeout_seconds: float = 1.5, poll_interval: float = 0.15):
    retries = max(1, int(timeout_seconds / poll_interval))
    for _ in range(retries):
        for backend in ("uia", "win32"):
            try:
                dialogs = Desktop(backend=backend).windows(class_name="#32770")
            except Exception:
                dialogs = []

            for dialog in dialogs:
                try:
                    if not dialog.is_visible():
                        continue
                except Exception:
                    pass

                texts = _get_dialog_texts(dialog)
                if not texts:
                    continue
                if _is_price_limit_dialog(dialog, texts):
                    return dialog, texts, backend
        sleep(poll_interval)
    return None, [], None


def _click_yes_on_dialog(dialog) -> bool:
    try:
        dialog.set_focus()
    except Exception:
        pass

    try:
        buttons = dialog.descendants(control_type="Button")
    except Exception:
        try:
            buttons = dialog.descendants()
        except Exception:
            buttons = []

    # 先按 control_id 精准点击
    for control_id in (6, 1, 1006):
        for button in buttons:
            try:
                cid = button.control_id()
            except Exception:
                continue
            if cid != control_id:
                continue
            try:
                button.click_input()
                return True
            except Exception:
                continue

    # 再按按钮文本兜底
    yes_keywords = ("是", "是(Y)", "Y", "Yes")
    for button in buttons:
        try:
            text = (button.window_text() or "").strip()
        except Exception:
            continue
        if text and any(keyword in text for keyword in yes_keywords):
            try:
                button.click_input()
                return True
            except Exception:
                continue

    return False


def handle_price_limit_popup_if_needed() -> None:
    dialog, texts, backend = _find_price_limit_dialog(timeout_seconds=1.5, poll_interval=0.15)
    if dialog is None:
        return

    print(f"检测到提示弹窗(backend={backend}): {' | '.join(texts)}")
    clicked = _click_yes_on_dialog(dialog)
    if not clicked:
        raise RuntimeError("检测到涨跌停限制提示弹窗，但未能点击“是”按钮")
    print("已点击“是”按钮处理涨跌停限制提示")

def main():
    backend, hwnd, title = find_window_handle(WINDOW_KEYWORD)
    if hwnd is None:
        raise RuntimeError(
            "未找到目标窗口。请确认客户端已打开，未处于精简模式，且脚本与客户端权限一致。"
        )

    print(f"命中窗口: backend={backend}, hwnd={hwnd}, title={title}")
    app = Application(backend=backend).connect(handle=hwnd)
    win = app.window(handle=hwnd)
    win.set_focus()
    goto_buy_page(win)
    print("已发送 F1，切换到买入下单页面")

    stock_code = "600779"
    stock_price = "35.9"
    buy_quantity = "500"
    input_stock_code(win, stock_code)
    input_stock_price(win, stock_price)
    input_buy_quantity(win, buy_quantity)
    buy_button = get_buy_button(win)
    print(
        f"已定位买入按钮: text='{buy_button.window_text()}', "
        f"control_id={buy_button.control_id()}"
    )
    # 如需实际点击下单，可取消下一行注释：
    buy_button.click_input()
    handle_price_limit_popup_if_needed()
    print(f"已填入证券代码: {stock_code}, 买入数量: {buy_quantity}")


if __name__ == "__main__":
    main()
