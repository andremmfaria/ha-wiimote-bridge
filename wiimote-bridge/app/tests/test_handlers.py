from wiimote_bridge.core import handlers


def test_handle_message_routes_button(monkeypatch):
    called = {}

    def fake_event_message(client, topic_prefix, wiimote_id, msg):
        called["events"] = (topic_prefix, wiimote_id, msg)

    def fake_button(client, topic_prefix, wiimote_id, button, down):
        called["button"] = (topic_prefix, wiimote_id, button, down)

    monkeypatch.setattr(handlers, "event_message", fake_event_message)
    monkeypatch.setattr(handlers, "button", fake_button)

    msg = {"type": "btn", "wiimote": 2, "btn": "A", "down": True}

    handlers.handle_message(object(), "wiimote", 7, msg)

    assert called["events"] == ("wiimote", 7, msg)
    assert called["button"] == ("wiimote", 7, "A", True)


def test_handle_message_routes_status(monkeypatch):
    called = {}

    def fake_event_message(client, topic_prefix, wiimote_id, msg):
        called["events"] = (topic_prefix, wiimote_id, msg)

    def fake_connected(client, topic_prefix, wiimote_id, connected):
        called["status"] = (topic_prefix, wiimote_id, connected)

    monkeypatch.setattr(handlers, "event_message", fake_event_message)
    monkeypatch.setattr(handlers, "connected", fake_connected)

    msg = {"type": "status", "wiimote": 1, "connected": False}

    handlers.handle_message(object(), "wiimote", 3, msg)

    assert called["events"] == ("wiimote", 3, msg)
    assert called["status"] == ("wiimote", 3, False)


def test_handle_message_routes_heartbeat(monkeypatch):
    called = {}
    msg = {"type": "heartbeat", "wiimote": 3, "battery": 80}

    def fake_event_message(client, topic_prefix, wiimote_id, payload):
        called["events"] = (topic_prefix, wiimote_id, payload)

    def fake_heartbeat(client, topic_prefix, wiimote_id, payload):
        called["heartbeat"] = (topic_prefix, wiimote_id, payload)

    monkeypatch.setattr(handlers, "event_message", fake_event_message)
    monkeypatch.setattr(handlers, "heartbeat", fake_heartbeat)

    handlers.handle_message(object(), "wiimote", 5, msg)

    assert called["events"] == ("wiimote", 5, msg)
    assert called["heartbeat"] == ("wiimote", 5, msg)


def test_handle_message_routes_battery(monkeypatch):
    called = {}
    msg = {"type": "battery", "wiimote": 4, "level": 92}

    def fake_event_message(client, topic_prefix, wiimote_id, payload):
        called["events"] = (topic_prefix, wiimote_id, payload)

    def fake_battery(client, topic_prefix, wiimote_id, level):
        called["battery"] = (topic_prefix, wiimote_id, level)

    monkeypatch.setattr(handlers, "event_message", fake_event_message)
    monkeypatch.setattr(handlers, "battery", fake_battery)

    handlers.handle_message(object(), "wiimote", 8, msg)

    assert called["events"] == ("wiimote", 8, msg)
    assert called["battery"] == ("wiimote", 8, 92)
