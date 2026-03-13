from wiimote_bridge.core import handlers


def test_handle_message_routes_button(monkeypatch):
    called = {}

    def fake_publish_event_message(client, topic_prefix, msg):
        called["events"] = (topic_prefix, msg)

    def fake_publish_button(client, topic_prefix, wiimote_id, button, down):
        called["button"] = (topic_prefix, wiimote_id, button, down)

    monkeypatch.setattr(handlers, "publish_event_message", fake_publish_event_message)
    monkeypatch.setattr(handlers, "publish_button", fake_publish_button)

    msg = {"type": "btn", "wiimote": 2, "btn": "A", "down": True}

    handlers.handle_message(object(), "wiimote", msg)

    assert called["events"] == ("wiimote", msg)
    assert called["button"] == ("wiimote", 2, "A", True)


def test_handle_message_routes_status(monkeypatch):
    called = {}

    def fake_publish_event_message(client, topic_prefix, msg):
        called["events"] = (topic_prefix, msg)

    def fake_publish_connected(client, topic_prefix, wiimote_id, connected):
        called["status"] = (topic_prefix, wiimote_id, connected)

    monkeypatch.setattr(handlers, "publish_event_message", fake_publish_event_message)
    monkeypatch.setattr(handlers, "publish_connected", fake_publish_connected)

    msg = {"type": "status", "wiimote": 1, "connected": False}

    handlers.handle_message(object(), "wiimote", msg)

    assert called["events"] == ("wiimote", msg)
    assert called["status"] == ("wiimote", 1, False)


def test_handle_message_routes_heartbeat(monkeypatch):
    called = {}
    msg = {"type": "heartbeat", "wiimote": 3, "battery": 80}

    def fake_publish_event_message(client, topic_prefix, payload):
        called["events"] = (topic_prefix, payload)

    def fake_publish_heartbeat(client, topic_prefix, wiimote_id, payload):
        called["heartbeat"] = (topic_prefix, wiimote_id, payload)

    monkeypatch.setattr(handlers, "publish_event_message", fake_publish_event_message)
    monkeypatch.setattr(handlers, "publish_heartbeat", fake_publish_heartbeat)

    handlers.handle_message(object(), "wiimote", msg)

    assert called["events"] == ("wiimote", msg)
    assert called["heartbeat"] == ("wiimote", 3, msg)


def test_handle_message_routes_battery(monkeypatch):
    called = {}
    msg = {"type": "battery", "wiimote": 4, "level": 92}

    def fake_publish_event_message(client, topic_prefix, payload):
        called["events"] = (topic_prefix, payload)

    def fake_publish_battery(client, topic_prefix, wiimote_id, level):
        called["battery"] = (topic_prefix, wiimote_id, level)

    monkeypatch.setattr(handlers, "publish_event_message", fake_publish_event_message)
    monkeypatch.setattr(handlers, "publish_battery", fake_publish_battery)

    handlers.handle_message(object(), "wiimote", msg)

    assert called["events"] == ("wiimote", msg)
    assert called["battery"] == ("wiimote", 4, 92)
