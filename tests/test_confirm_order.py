"""HTTP/GUI contract tests. No desktop, keyboard, OCR or network is used."""
import importlib.util
from pathlib import Path
import sys
import threading
import time
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_source(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def api(monkeypatch):
    # Stub only external boundaries at import time; execute both production
    # WindowService (including replacement/readback) and Flask route code.
    stubs = {name: ModuleType(name) for name in (
        'win32gui', 'win32con', 'win32api', 'win32clipboard', 'win32process',
        'psutil', 'pywinauto', 'pywinauto.clipboard', 'pyautogui',
        'src.util.logger', 'src.service.proxy_service', 'config.key_config',
    )}
    stubs['pywinauto'].Desktop = Mock(side_effect=AssertionError('real desktop access'))
    stubs['pywinauto.clipboard'].GetData = Mock(side_effect=AssertionError('clipboard access'))
    stubs['src.util.logger'].Logger = Mock()
    stubs['src.service.proxy_service'].ProxyService = Mock()
    stubs['config.key_config'].KEY_MAP = {}
    with patch.dict(sys.modules, stubs):
        window_module = load_source('_confirm_test_window', 'src/service/window_service.py')
        with patch.dict(sys.modules, {'src.service.window_service': window_module}):
            flask_module = load_source('_confirm_test_flask', 'src/service/flask_service.py')
    # Replace module-local clocks, not the global time module used by threads.
    monkeypatch.setattr(window_module, 'time', SimpleNamespace(sleep=lambda _: None))
    monkeypatch.setattr(flask_module, 'time', SimpleNamespace(
        sleep=lambda _: None, monotonic=time.monotonic, time=time.time))

    service = window_module.WindowService()
    events = []
    state = SimpleNamespace(available='1000', failure=None, mismatch=None)

    class Edit:
        text = '9999'  # Pre-existing value must be replaced after refresh.
        reads = 0

        def control_id(self):
            return 1034

        def window_text(self):
            assert app.gui_lock.locked()
            self.reads += 1
            events.append(('read', self.text))
            if state.failure == 'available_read' or (self.reads > 1 and state.failure == 'readback'):
                raise RuntimeError('read failed')
            return self.text

        def set_focus(self):
            assert app.gui_lock.locked()
            events.append(('focus', 1034))
            if state.failure == 'focus':
                raise RuntimeError('focus failed')

        def set_edit_text(self, text):
            assert app.gui_lock.locked()
            events.append(('replace', text))
            if state.failure == 'write':
                raise RuntimeError('write failed')
            if state.mismatch == 'append':
                self.text += text
            else:
                self.text = text if state.mismatch is None else state.mismatch

    edit = Edit()

    class Button:
        def __init__(self, control_id):
            self.id = control_id

        def control_id(self):
            return self.id

        def click_input(self):
            assert app.gui_lock.locked()
            events.append(('click', self.id))
            if self.id == 1528:
                edit.text = state.available
                edit.reads = 0

    controls = [edit] + [Button(i) for i in (1528, 1006, 12092, 12093, 12094, 12095)]
    dialog = SimpleNamespace(descendants=lambda: controls)
    service.get_target_window = Mock(return_value=dialog)
    monkeypatch.setattr(flask_module, 'WindowService', lambda: service)
    app = flask_module.FlaskApp(controller=Mock())
    app.app.config['TESTING'] = True
    yield SimpleNamespace(app=app, client=app.app.test_client(), service=service,
                          edit=edit, events=events, state=state, controls=controls)
    assert not app.gui_lock.locked(), 'GUI lock leaked'
    assert app.gui_lock_owner is None
    sys.modules.pop('_confirm_test_window', None)
    sys.modules.pop('_confirm_test_flask', None)


@pytest.mark.parametrize('amount', ['', '0', '-1', '1.5', 'abc', ' ', '+3', '1_000', '３'])
def test_invalid_amount_rejected_before_gui(api, amount):
    response = api.client.get('/confirm_order', query_string={'amount': amount})
    assert response.status_code == 400
    api.service.get_target_window.assert_not_called()
    assert api.events == []


@pytest.mark.parametrize('position', ['', '2', 'bad'])
def test_amount_position_conflict_before_gui(api, position):
    response = api.client.get('/confirm_order', query_string={'amount': '300', 'position': position})
    assert response.status_code == 400
    api.service.get_target_window.assert_not_called()


@pytest.mark.parametrize('amount', ['300', '301', '1000', '1', '00300'])
def test_exact_amount_replaces_original_then_confirms(api, amount):
    response = api.client.get('/confirm_order', query_string={'amount': amount})
    expected = int(amount)
    assert response.status_code == 200
    assert response.json['data'] == {
        'available_amount': 1000, 'position': None, 'order_amount': expected,
    }
    assert api.edit.text == str(expected)
    assert api.events == [
        ('click', 1528), ('read', '1000'), ('focus', 1034),
        ('replace', str(expected)), ('read', str(expected)), ('click', 1006),
    ]


def test_over_limit_stops_before_writing_or_confirming(api):
    response = api.client.get('/confirm_order?amount=1001')
    assert response.status_code == 400
    assert api.events == [('click', 1528), ('read', '1000')]


@pytest.mark.parametrize('available,status', [
    ('', 400), ('0', 400), ('00', 400), ('-100', 400), ('1.5', 500), ('abc', 500),
])
def test_invalid_available_never_confirms(api, available, status):
    api.state.available = available
    assert api.client.get('/confirm_order?amount=1').status_code == status
    assert ('click', 1006) not in api.events
    assert not any(e[0] == 'replace' for e in api.events)


@pytest.mark.parametrize('failure', ['available_read', 'focus', 'write', 'readback'])
def test_input_or_read_failure_never_confirms_and_releases_lock(api, failure):
    api.state.failure = failure
    assert api.client.get('/confirm_order?amount=300').status_code == 500
    assert ('click', 1006) not in api.events
    assert len([e for e in api.events if e[0] == 'replace']) <= 1
    assert not api.app.gui_lock.locked()
    api.state.failure = None
    assert api.client.get('/confirm_order?amount=300').status_code == 200


@pytest.mark.parametrize('mismatch', ['append', '', '301', 'bad'])
def test_readback_mismatch_never_confirms(api, mismatch):
    api.state.mismatch = mismatch
    assert api.client.get('/confirm_order?amount=300').status_code == 500
    assert ('click', 1006) not in api.events
    assert api.events.count(('replace', '300')) == 1


def test_missing_window(api):
    api.service.get_target_window.return_value = None
    assert api.client.get('/confirm_order?amount=300').status_code == 500
    assert api.events == []


@pytest.mark.parametrize('missing', [1528, 1034, 1006])
def test_missing_control(api, missing):
    api.controls[:] = [c for c in api.controls if c.control_id() != missing]
    assert api.client.get('/confirm_order?amount=300').status_code == 500
    assert ('click', 1006) not in api.events


def test_input_disappears_after_available_read(api):
    read = api.edit.window_text

    def read_then_remove():
        text = read()
        api.controls.remove(api.edit)
        return text

    api.edit.window_text = read_then_remove
    assert api.client.get('/confirm_order?amount=300').status_code == 500
    assert api.events == [('click', 1528), ('read', '1000')]


@pytest.mark.parametrize('position,expected,button', [
    ('1', 1000, 12092), ('2', 500, 12093), ('3', 300, 12094), ('4', 200, 12095),
])
def test_original_position_behavior(api, position, expected, button):
    response = api.client.get('/confirm_order', query_string={'position': position})
    assert response.status_code == 200
    assert response.json['data'] == {
        'available_amount': 1000, 'position': int(position), 'order_amount': expected,
    }
    assert response.json['message'] == f'下单确认成功,仓位:{position},可用数量:1000,下单数量:{expected}'
    assert api.events == [('click', 1528), ('read', '1000'), ('click', button), ('click', 1006)]


def test_default_full_position_behavior(api):
    api.state.available = '1051'
    response = api.client.get('/confirm_order')
    assert response.status_code == 200
    assert response.json['data'] == {'available_amount': 1051, 'position': None, 'order_amount': 1051}
    assert response.json['message'] == '下单确认成功,满仓,可用数量:1051,下单数量:1051'
    assert api.events == [('click', 1528), ('read', '1051'), ('click', 1006)]


@pytest.mark.parametrize('position', ['', '0', '5', 'abc', '1.5'])
def test_original_position_validation(api, position):
    assert api.client.get('/confirm_order', query_string={'position': position}).status_code == 400
    api.service.get_target_window.assert_not_called()


def test_original_position_too_small(api):
    api.state.available = '199'
    assert api.client.get('/confirm_order?position=2').status_code == 400
    assert api.events == [('click', 1528), ('read', '199')]


def test_busy_lock_never_touches_gui(api):
    api.app.gui_lock_timeout = 0.001
    with api.app.gui_lock:
        assert api.client.get('/confirm_order?amount=300').status_code == 429
        api.service.get_target_window.assert_not_called()
    assert api.client.get('/confirm_order?amount=300').status_code == 200


def test_requests_cannot_interleave_during_write_readback_confirm(api):
    entered_write = threading.Event()
    release_write = threading.Event()
    second_waiting = threading.Event()
    results = []
    replace = api.edit.set_edit_text

    class ObservedLock:
        def __init__(self):
            self.lock = threading.Lock()

        def acquire(self, timeout):
            if self.lock.locked():
                second_waiting.set()
            return self.lock.acquire(timeout=timeout)

        def release(self):
            self.lock.release()

        def locked(self):
            return self.lock.locked()

    api.app.gui_lock = ObservedLock()

    def blocked_replace(text):
        replace(text)
        if text == '300':
            entered_write.set()
            assert release_write.wait(3), 'test failed to release writer'

    api.edit.set_edit_text = blocked_replace

    def request(amount):
        with api.app.app.test_client() as client:
            results.append(client.get('/confirm_order', query_string={'amount': amount}).status_code)

    first = threading.Thread(target=request, args=('300',))
    second = threading.Thread(target=request, args=('301',))
    first.start()
    try:
        assert entered_write.wait(3)
        second.start()
        assert second_waiting.wait(3)
        assert api.service.get_target_window.call_count == 1
        assert ('click', 1006) not in api.events
    finally:
        release_write.set()
        first.join(3)
        if second.ident is not None:
            second.join(3)
    assert not first.is_alive() and not second.is_alive()
    assert results == [200, 200]
    assert api.events == [
        ('click', 1528), ('read', '1000'), ('focus', 1034),
        ('replace', '300'), ('read', '300'), ('click', 1006),
        ('click', 1528), ('read', '1000'), ('focus', 1034),
        ('replace', '301'), ('read', '301'), ('click', 1006),
    ]
