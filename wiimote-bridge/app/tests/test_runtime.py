import threading

import wiimote_bridge.core.run as run_module
from wiimote_bridge.utils.config import RadioConfig


class _FakeClient:
    def __init__(self):
        self.stopped = False
        self.disconnected = False
        self.published = []

    def loop_stop(self):
        self.stopped = True

    def disconnect(self):
        self.disconnected = True

    def is_connected(self):
        return True

    def publish(self, topic, payload, retain=False):
        self.published.append((topic, payload, retain))

        class _Result:
            rc = 0

            @staticmethod
            def wait_for_publish():
                return None

        return _Result()


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


# ---------------------------------------------------------------------------
# run() tests — threading behaviour
# ---------------------------------------------------------------------------

def test_run_spawns_thread_per_radio(monkeypatch):
    fake_client = _FakeClient()
    spawned = []

    class FakeThread:
        def __init__(self, target, args, daemon, name):
            spawned.append({"target": target, "args": args, "name": name})

        def start(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setattr(run_module.threading, "Thread", FakeThread)
    monkeypatch.setenv(
        "RADIOS",
        '[{"port":"/dev/ttyUSB0","baud":115200,"controller_id":1},'
        '{"port":"/dev/ttyUSB1","baud":115200,"controller_id":2}]',
    )
    monkeypatch.setattr(run_module, "connect_mqtt", lambda _settings: fake_client)
    monkeypatch.setattr(run_module, "configure_logging", lambda level: level)
    _patch_signal_handlers(monkeypatch)

    result = run_module.run()

    assert result == 0
    assert len(spawned) == 2
    assert spawned[0]["args"][0].controller_id == 1
    assert spawned[1]["args"][0].controller_id == 2
    assert spawned[0]["name"] == "radio-1"
    assert spawned[1]["name"] == "radio-2"
    assert fake_client.stopped is True
    assert fake_client.disconnected is True


def test_run_publishes_discovery_for_all_radios(monkeypatch):
    fake_client = _FakeClient()
    called = {}

    class FakeThread:
        def __init__(self, target, args, daemon, name):
            pass

        def start(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setattr(run_module.threading, "Thread", FakeThread)
    monkeypatch.setenv(
        "RADIOS",
        '[{"port":"/dev/ttyUSB0","baud":115200,"controller_id":1},'
        '{"port":"/dev/ttyUSB1","baud":115200,"controller_id":4}]',
    )
    monkeypatch.setattr(run_module, "connect_mqtt", lambda _settings: fake_client)
    monkeypatch.setattr(run_module, "configure_logging", lambda level: level)

    def fake_publish_discovery_configs(_client, _topic_prefix, wiimote_ids):
        called["args"] = (_topic_prefix, list(wiimote_ids))

    monkeypatch.setattr(run_module, "publish_discovery_configs", fake_publish_discovery_configs)
    _patch_signal_handlers(monkeypatch)

    result = run_module.run()

    assert result == 0
    assert called["args"] == ("wiimote", [1, 4])


def test_run_skips_discovery_when_disabled(monkeypatch):
    fake_client = _FakeClient()
    called = {"count": 0}

    class FakeThread:
        def __init__(self, target, args, daemon, name):
            pass

        def start(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setattr(run_module.threading, "Thread", FakeThread)
    monkeypatch.setenv("DISCOVER_ENABLED", "false")
    monkeypatch.setattr(run_module, "connect_mqtt", lambda _settings: fake_client)
    monkeypatch.setattr(run_module, "configure_logging", lambda level: level)

    def fake_publish_discovery_configs(_client, _topic_prefix, wiimote_ids):
        called["count"] += 1

    monkeypatch.setattr(run_module, "publish_discovery_configs", fake_publish_discovery_configs)
    _patch_signal_handlers(monkeypatch)

    result = run_module.run()

    assert result == 0
    assert called["count"] == 0


def test_run_uses_configured_log_level(monkeypatch):
    fake_client = _FakeClient()
    configured = {}

    class FakeThread:
        def __init__(self, target, args, daemon, name):
            pass

        def start(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setattr(run_module.threading, "Thread", FakeThread)
    monkeypatch.setenv("LOG_LEVEL", "warning")
    monkeypatch.setattr(run_module, "connect_mqtt", lambda _settings: fake_client)

    def fake_configure_logging(level_name):
        configured["level"] = level_name
        return level_name

    monkeypatch.setattr(run_module, "configure_logging", fake_configure_logging)
    _patch_signal_handlers(monkeypatch)

    result = run_module.run()

    assert result == 0
    assert configured["level"] == "warning"


# ---------------------------------------------------------------------------
# run_radio() tests — serial reading behaviour
# ---------------------------------------------------------------------------

def test_run_radio_processes_message(monkeypatch):
    stop_event = threading.Event()
    radio = RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=3)
    fake_serial = _FakeSerial([b'{"type":"btn","wiimote":0,"btn":"A","down":true}\n'])
    seen = {}

    def fake_handle_message(client, topic_prefix, controller_id, msg):
        seen["args"] = (topic_prefix, controller_id, msg)
        stop_event.set()

    monkeypatch.setattr(run_module, "open_serial", lambda port, baud: fake_serial)
    monkeypatch.setattr(run_module, "handle_message", fake_handle_message)

    run_module.run_radio(radio, object(), "wiimote", stop_event)

    assert seen["args"] == (
        "wiimote",
        3,
        {"type": "btn", "wiimote": 0, "btn": "A", "down": True},
    )
    assert fake_serial.closed is True


def test_run_radio_handles_open_serial_failure(monkeypatch):
    stop_event = threading.Event()
    radio = RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=1)

    def fake_open_serial(port, baud):
        stop_event.set()
        raise RuntimeError("port busy")

    monkeypatch.setattr(run_module, "open_serial", fake_open_serial)

    run_module.run_radio(radio, object(), "wiimote", stop_event)


def test_run_radio_handles_serial_exception(monkeypatch):
    stop_event = threading.Event()
    radio = RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=1)

    class BoomSerial(_FakeSerial):
        def readline(self):
            stop_event.set()
            raise run_module.serial.SerialException("serial failure")

    fake_serial = BoomSerial([])
    monkeypatch.setattr(run_module, "open_serial", lambda port, baud: fake_serial)

    run_module.run_radio(radio, object(), "wiimote", stop_event)

    assert fake_serial.closed is True


def test_run_radio_handles_unexpected_exception(monkeypatch):
    stop_event = threading.Event()
    radio = RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=1)
    fake_serial = _FakeSerial([b'{"type":"status","connected":true}\n'])

    monkeypatch.setattr(run_module, "open_serial", lambda port, baud: fake_serial)

    def exploding_handle(client, topic_prefix, controller_id, msg):
        stop_event.set()
        raise ValueError("bad")

    monkeypatch.setattr(run_module, "handle_message", exploding_handle)

    run_module.run_radio(radio, object(), "wiimote", stop_event)

    assert fake_serial.closed is True


def test_run_radio_uses_controller_id(monkeypatch):
    stop_event = threading.Event()
    radio = RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=9)
    fake_serial = _FakeSerial([b'{"type":"status","connected":true}\n'])
    seen = {}

    monkeypatch.setattr(run_module, "open_serial", lambda port, baud: fake_serial)

    def fake_handle_message(client, topic_prefix, controller_id, msg):
        seen["controller_id"] = controller_id
        stop_event.set()

    monkeypatch.setattr(run_module, "handle_message", fake_handle_message)

    run_module.run_radio(radio, object(), "wiimote", stop_event)

    assert seen["controller_id"] == 9

