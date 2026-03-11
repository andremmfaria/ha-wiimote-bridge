from wiimote_bridge.core import handlers


def test_handle_message_routes_button(monkeypatch):
    called = {}

    def fake_publish_button(client, topic_prefix, wiimote_id, button, down):
        called["button"] = (topic_prefix, wiimote_id, button, down)

    monkeypatch.setattr(handlers, "publish_button", fake_publish_button)

    handlers.handle_message(object(), "wiimote", {"type": "btn", "wiimote": 2, "btn": "A", "down": True})

    assert called["button"] == ("wiimote", 2, "A", True)


def test_handle_message_routes_status(monkeypatch):
    called = {}

    def fake_publish_connected(client, topic_prefix, wiimote_id, connected):
        called["status"] = (topic_prefix, wiimote_id, connected)

    monkeypatch.setattr(handlers, "publish_connected", fake_publish_connected)

    handlers.handle_message(object(), "wiimote", {"type": "status", "wiimote": 1, "connected": False})

    assert called["status"] == ("wiimote", 1, False)


def test_handle_message_routes_heartbeat(monkeypatch):
    called = {}
    msg = {"type": "heartbeat", "wiimote": 3, "battery": 80}

    def fake_publish_heartbeat(client, topic_prefix, wiimote_id, payload):
        called["heartbeat"] = (topic_prefix, wiimote_id, payload)

    monkeypatch.setattr(handlers, "publish_heartbeat", fake_publish_heartbeat)

    handlers.handle_message(object(), "wiimote", msg)

    assert called["heartbeat"] == ("wiimote", 3, msg)
