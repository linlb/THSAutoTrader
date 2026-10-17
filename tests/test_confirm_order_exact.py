"""只运行 Flask 路由；桌面模块、窗口、键盘和网络服务全部替身。"""
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, call

import pytest


@pytest.fixture
def service(monkeypatch):
    for name, attributes in {
        'pyautogui': {},
        'src.service.window_service': {'WindowService': MagicMock},
        'src.service.proxy_service': {'ProxyService': MagicMock},
        'src.util.logger': {'Logger': MagicMock()},
    }.items():
        stub = ModuleType(name)
        stub.__dict__.update(attributes)
        monkeypatch.setitem(sys.modules, name, stub)
    spec = importlib.util.spec_from_file_location(
        'flask_exact_test', Path(__file__).parents[1] / 'src/service/flask_service.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.time, 'sleep', lambda _: None)
    app = module.FlaskApp()
    element = MagicMock()
    element.window_text.return_value = '300'
    window = object()
    app.window_service.get_target_window.return_value = window
    app.window_service.find_element_in_window.return_value = element
    return SimpleNamespace(app=app, client=app.app.test_client(),
                           gui=app.window_service, element=element, window=window)


def test_exact_quantity_readback_before_single_submit(service):
    trace = MagicMock()
    trace.attach_mock(service.element, 'quantity')
    trace.attach_mock(service.gui.click_element, 'click')
    response = service.client.get('/confirm_order_exact?amount=300')
    assert response.status_code == 200
    assert response.json['data'] == {
        'order_amount': 300, 'quantity_verified': True, 'price_verified': False}
    assert trace.mock_calls == [
        call.quantity.set_focus(), call.quantity.type_keys('^a{BACKSPACE}'),
        call.quantity.type_keys('300'), call.quantity.window_text(),
        call.click(service.window, 1006, retries=1)]
    service.gui.find_element_in_window.assert_called_once_with(service.window, 1034)
    assert service.app.gui_lock_owner is None
    assert not service.app.gui_lock.locked()


@pytest.mark.parametrize('query', [
    '', 'amount=', 'amount=0', 'amount=-100', 'amount=50', 'amount=100.0',
    'amount=1e2', 'amount=%2B100', 'amount=%20100', 'amount=１００',
    'amount=abc', 'amount=100&amount=200', 'amount=100&position=2',
    'amount=100&position=', 'amount=100&price=10', 'position=2',
])
def test_invalid_parameters_never_touch_gui(service, query):
    response = service.client.get('/confirm_order_exact?' + query)
    assert response.status_code == 400
    service.gui.get_target_window.assert_not_called()
    service.gui.click_element.assert_not_called()


@pytest.mark.parametrize('readback', ['', '200', '3000', '300.0', '３００', '300 shares'])
def test_readback_failure_never_submits(service, readback):
    service.element.window_text.return_value = readback
    assert service.client.get('/confirm_order_exact?amount=300').status_code == 500
    service.gui.click_element.assert_not_called()


@pytest.mark.parametrize('failure', ['window', 'element', 'focus', 'clear', 'write', 'read'])
def test_gui_failure_never_submits_and_releases_lock(service, failure):
    if failure == 'window':
        service.gui.get_target_window.return_value = None
    elif failure == 'element':
        service.gui.find_element_in_window.return_value = None
    elif failure == 'focus':
        service.element.set_focus.side_effect = RuntimeError('focus failed')
    elif failure == 'clear':
        service.element.type_keys.side_effect = RuntimeError('clear failed')
    elif failure == 'write':
        service.element.type_keys.side_effect = [None, RuntimeError('write failed')]
    else:
        service.element.window_text.side_effect = RuntimeError('read failed')
    response = service.client.get('/confirm_order_exact?amount=300')
    assert response.status_code == 500
    service.gui.click_element.assert_not_called()
    assert not service.app.gui_lock.locked()


def test_click_exception_does_not_retry(service):
    service.gui.click_element.side_effect = RuntimeError('could already have submitted')
    response = service.client.get('/confirm_order_exact?amount=300')
    assert response.status_code == 500
    service.gui.click_element.assert_called_once_with(service.window, 1006, retries=1)
    assert not service.app.gui_lock.locked()


def test_gui_lock_blocks_exact_route(service):
    service.app.gui_lock_timeout = 0
    service.app.gui_lock.acquire()
    try:
        assert service.client.get('/confirm_order_exact?amount=300').status_code == 429
        service.gui.get_target_window.assert_not_called()
    finally:
        service.app.gui_lock.release()


def test_exact_route_only_accepts_get(service):
    assert service.client.post('/confirm_order_exact?amount=300').status_code == 405
    service.gui.get_target_window.assert_not_called()


@pytest.mark.parametrize('query,amount,buttons', [
    ('', 600, [1528, 1006]),
    ('?position=2', 300, [1528, 12093, 1006]),
])
def test_legacy_confirm_keeps_existing_behavior(service, query, amount, buttons):
    service.element.window_text.return_value = '600'
    response = service.client.get('/confirm_order' + query)
    assert response.status_code == 200
    assert response.json['data']['order_amount'] == amount
    assert service.gui.click_element.call_args_list == [call(service.window, b) for b in buttons]
    service.element.type_keys.assert_not_called()
