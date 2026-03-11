import signal

import wiimote_bridge.core.run as run_module



class _FakeClient:
    def __init__(self):
        self.stopped = False
        self.disconnected = False

    def loop_stop(self):
        self.stopped = True

    def disconnect(self):
        self.disconnected = True


class _FakeSerial:
    def __init__(self, lines):
        self._lines = list(lines)
        self.closed = False

    def readline(self):
        if self._lines:
            return self._lines.pop(0)
        return b""

    def close(self):
        self.closed = True


def _patch_signal_handlers(monkeypatch):
    handlers = {}

    def fake_signal(sig, handler):
        handlers[sig] = handler

    monkeypatch.setattr(run_module.signal, "signal", fake_signal)
    return handlers


def test_run_processes_message_and_shuts_down(monkeypatch):
    handlers = _patch_signal_handlers(monkeypatch)
    fake_client = _FakeClient()
    fake_serial = _FakeSerial([b'{"type":"btn","wiimote":1,"btn":"A","down":true}\n'])
    seen = {}

    def fake_connect(_settings):
        return fake_client

    def fake_open_serial(_settings):
        return fake_serial

    def fake_handle_message(_client, _topic_prefix, _msg):
        seen["called"] = True
        handlers[signal.SIGTERM](signal.SIGTERM, None)

    monkeypatch.setattr(run_module, "connect_mqtt", fake_connect)
    monkeypatch.setattr(run_module, "open_serial", fake_open_serial)
    monkeypatch.setattr(run_module, "handle_message", fake_handle_message)

    result = run_module.run()

    assert result == 0
    assert seen["called"] is True
    assert fake_serial.closed is True
    assert fake_client.stopped is True
    assert fake_client.disconnected is True


def test_run_handles_open_serial_failure(monkeypatch):
    handlers = _patch_signal_handlers(monkeypatch)
    fake_client = _FakeClient()

    monkeypatch.setattr(run_module, "connect_mqtt", lambda _settings: fake_client)
    monkeypatch.setattr(run_module, "open_serial", lambda _settings: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(run_module.time, "sleep", lambda _seconds: handlers[signal.SIGTERM](signal.SIGTERM, None))

    result = run_module.run()

    assert result == 0
    assert fake_client.stopped is True
    assert fake_client.disconnected is True


def test_run_handles_serial_exception(monkeypatch):
    handlers = _patch_signal_handlers(monkeypatch)
    fake_client = _FakeClient()

    class BoomSerial(_FakeSerial):
        def readline(self):
            raise run_module.serial.SerialException("serial failure")

    fake_serial = BoomSerial([])
    monkeypatch.setattr(run_module, "connect_mqtt", lambda _settings: fake_client)
    monkeypatch.setattr(run_module, "open_serial", lambda _settings: fake_serial)
    monkeypatch.setattr(run_module.time, "sleep", lambda _seconds: handlers[signal.SIGTERM](signal.SIGTERM, None))

    result = run_module.run()

    assert result == 0
    assert fake_serial.closed is True
    assert fake_client.stopped is True
    assert fake_client.disconnected is True


def test_run_handles_unexpected_exception(monkeypatch):
    handlers = _patch_signal_handlers(monkeypatch)
    fake_client = _FakeClient()
    fake_serial = _FakeSerial([b'{"type":"status","connected":true}\n'])

    monkeypatch.setattr(run_module, "connect_mqtt", lambda _settings: fake_client)
    monkeypatch.setattr(run_module, "open_serial", lambda _settings: fake_serial)
    monkeypatch.setattr(run_module, "handle_message", lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad")))
    monkeypatch.setattr(run_module.time, "sleep", lambda _seconds: handlers[signal.SIGTERM](signal.SIGTERM, None))

    result = run_module.run()

    assert result == 0
    assert fake_serial.closed is True
    assert fake_client.stopped is True
    assert fake_client.disconnected is True
