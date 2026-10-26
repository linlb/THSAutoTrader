"""在无 Windows 桌面的环境中验证提交后检查，所有 GUI 操作均为 mock。"""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest


class Clock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, duration):
        self.now += duration


@pytest.fixture
def runtime(monkeypatch):
    # 仅替换平台和外围依赖，加载真实窗口服务与 Flask 路由。
    gui = Mock()
    dependencies = {
        name: Mock() for name in (
            'win32con', 'win32api', 'win32clipboard', 'win32process',
            'psutil', 'pywinauto', 'pywinauto.clipboard', 'pyautogui',
            'src.util.logger', 'src.service.proxy_service',
        )
    }
    dependencies['win32gui'] = gui
    for name, module in dependencies.items():
        monkeypatch.setitem(sys.modules, name, module)

    root = Path(__file__).resolve().parents[1]

    def load(name, filename):
        spec = importlib.util.spec_from_file_location(name, root / filename)
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
        return module

    windows = load('src.service.window_service', 'src/service/window_service.py')
    flask = load('_test_flask_service', 'src/service/flask_service.py')
    clock = Clock()
    monkeypatch.setattr(windows, 'time', clock)
    # HTTP 刷新/仓位等待不消耗真实时间，也不影响窗口轮询时钟。
    monkeypatch.setattr(flask, 'time', SimpleNamespace(
        monotonic=clock.monotonic, sleep=lambda _: None,
    ))
    app = flask.FlaskApp()
    window = Mock(handle=12345)
    service = app.window_service
    service.get_target_window = Mock(return_value=window)
    service.click_element = Mock()
    service.find_element_in_window = Mock()
    service.find_element_in_window.return_value.window_text.return_value = '1000'
    return SimpleNamespace(
        gui=gui, clock=clock, app=app, service=service, window=window,
        client=app.app.test_client(),
    )


@pytest.mark.parametrize('state', ['destroyed', 'hidden', 'delayed'])
def test_closed_dialog_keeps_existing_success_response(runtime, state):
    r = runtime
    if state == 'destroyed':
        r.gui.IsWindow.return_value = False
    elif state == 'hidden':
        r.gui.IsWindowVisible.return_value = False
    else:
        r.gui.IsWindow.side_effect = [True, True, False]
        r.gui.IsWindowVisible.return_value = True

    response = r.client.get('/confirm_order?position=2')

    assert response.status_code == 200
    assert response.json == {
        'status': 'success',
        'message': '下单确认成功,仓位:2,可用数量:1000,下单数量:500',
        'data': {'available_amount': 1000, 'position': 2, 'order_amount': 500},
    }
    assert r.service.click_element.call_args_list == [
        call(r.window, 1528), call(r.window, 12093),
        call(r.window, 1006, retries=1),
    ]
    # 后检不得重新枚举空标题窗口，也不得观察其他句柄。
    r.service.get_target_window.assert_called_once()
    assert all(args == call(12345) for args in r.gui.IsWindow.call_args_list)
    assert not r.app.gui_lock.locked()
    if state == 'delayed':
        assert r.clock.now == pytest.approx(0.4)


def test_visible_dialog_times_out_without_another_click(runtime):
    r = runtime
    r.gui.IsWindow.return_value = True
    r.gui.IsWindowVisible.return_value = True

    response = r.client.get('/confirm_order')

    assert response.status_code == 500
    assert response.json['status'] == 'error'
    assert '提交后弹窗未关闭' in response.json['message']
    assert '12345' in response.json['message']
    assert r.clock.now == pytest.approx(2.0)
    assert r.service.click_element.call_args_list == [
        call(r.window, 1528), call(r.window, 1006, retries=1),
    ]
    assert not r.app.gui_lock.locked()


@pytest.mark.parametrize('method', ['IsWindow', 'IsWindowVisible'])
def test_unreadable_dialog_state_is_unknown_not_success(runtime, method):
    r = runtime
    getattr(r.gui, method).side_effect = RuntimeError('读取失败')

    response = r.client.get('/confirm_order')

    assert response.status_code == 500
    assert response.json['status'] == 'error'
    assert '提交后弹窗状态未知' in response.json['message']
    assert '需核验委托和成交' in response.json['message']
    assert r.service.click_element.call_args_list == [
        call(r.window, 1528), call(r.window, 1006, retries=1),
    ]
    assert not r.app.gui_lock.locked()


@pytest.mark.parametrize('path,quantity,missing,status', [
    ('/confirm_order?position=5', '1000', False, 400),
    ('/confirm_order?position=abc', '1000', False, 400),
    ('/confirm_order', '1000', True, 500),
    ('/confirm_order', '0', False, 400),
    ('/confirm_order', '', False, 400),
    ('/confirm_order', 'abc', False, 500),
    ('/confirm_order?position=4', '100', False, 400),
])
def test_existing_validation_does_not_submit(runtime, path, quantity, missing, status):
    r = runtime
    r.service.find_element_in_window.return_value.window_text.return_value = quantity
    if missing:
        r.service.get_target_window.return_value = None

    response = r.client.get(path)

    assert response.status_code == status
    assert response.json['status'] == 'error'
    assert not any(args.args[1] == 1006 for args in r.service.click_element.call_args_list)
    r.gui.IsWindow.assert_not_called()
    assert not r.app.gui_lock.locked()


def test_click_error_does_not_retry_or_claim_success(runtime):
    r = runtime
    r.service.click_element.side_effect = [None, RuntimeError('点击失败')]

    response = r.client.get('/confirm_order')

    assert response.status_code == 500
    assert '点击失败' in response.json['message']
    assert r.service.click_element.call_args_list == [
        call(r.window, 1528), call(r.window, 1006, retries=1),
    ]
    r.gui.IsWindow.assert_not_called()
    assert not r.app.gui_lock.locked()


def test_postcheck_keeps_gui_lock_until_observation_finishes(runtime):
    r = runtime

    def observe(hwnd):
        assert hwnd == 12345
        assert r.app.gui_lock.locked()
        return False

    r.gui.IsWindow.side_effect = observe
    response = r.client.get('/confirm_order')

    assert response.status_code == 200
    assert response.json['data'] == {
        'available_amount': 1000, 'position': None, 'order_amount': 1000,
    }
    assert not r.app.gui_lock.locked()
