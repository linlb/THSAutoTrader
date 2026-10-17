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


@pytest.mark.parametrize('query', [
    '', 'amount=300', 'amount=0', 'amount=-100', 'amount=50',
    'amount=100&amount=200', 'amount=100&position=2',
    'amount=300&stockCode=600000&side=buy&price=10.00',
    'amount=300&price_verified=true&quantity_verified=true',
    'amount=300&enabled=true&debug=true',
])
def test_exact_route_disabled_without_any_gui_operation(service, query):
    response = service.client.get('/confirm_order_exact?' + query)
    assert response.status_code == 503
    assert response.json['status'] == 'error'
    assert response.json['code'] == 'EXACT_ORDER_NOT_VALIDATED'
    assert 'data' not in response.json
    assert service.gui.mock_calls == []
    assert service.element.mock_calls == []


def test_disabled_route_does_not_wait_for_gui_or_release_another_owner_lock(service):
    service.app.gui_lock.acquire()
    try:
        response = service.client.get('/confirm_order_exact?amount=300')
        assert response.status_code == 503
        assert service.app.gui_lock.locked()
        assert service.gui.mock_calls == []
    finally:
        service.app.gui_lock.release()


def test_exact_route_only_accepts_get(service):
    assert service.client.post('/confirm_order_exact?amount=300').status_code == 405
    assert service.gui.mock_calls == []


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
