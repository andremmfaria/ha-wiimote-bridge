from wiimote_bridge.transport import mqtt_client
from wiimote_bridge.utils.config import Settings


def test_publish_button_formats_topic_and_payload(monkeypatch):
    called = {}

    def fake_publish(client, topic, payload, retain=False):
        called["data"] = (topic, payload, retain)

    monkeypatch.setattr(mqtt_client, "mqtt_publish", fake_publish)

    mqtt_client.publish_button(object(), "wiimote", 1, "A", True)

    assert called["data"] == ("wiimote/1/button/A", "ON", False)


def test_publish_connected_retained(monkeypatch):
    called = {}

    def fake_publish(client, topic, payload, retain=False):
        called["data"] = (topic, payload, retain)

    monkeypatch.setattr(mqtt_client, "mqtt_publish", fake_publish)

    mqtt_client.publish_connected(object(), "wiimote", 1, False)

    assert called["data"] == ("wiimote/1/status/connected", "false", True)


def test_connect_mqtt_sets_auth_and_starts_loop(monkeypatch):
    calls = {}

    class FakeClient:
        def __init__(self, client_id, clean_session):
            calls["init"] = (client_id, clean_session)

        def username_pw_set(self, username, password):
            calls["auth"] = (username, password)

        def connect(self, host, port, keepalive):
            calls["connect"] = (host, port, keepalive)

        def loop_start(self):
            calls["loop_start"] = True

    monkeypatch.setattr(mqtt_client.mqtt, "Client", FakeClient)

    settings = Settings(
        serial_port="/dev/ttyUSB0",
        serial_baud=115200,
        mqtt_host="broker.local",
        mqtt_port=2883,
        mqtt_username="u",
        mqtt_password="p",
        topic_prefix="wiimote",
    )

    client = mqtt_client.connect_mqtt(settings)

    assert client is not None
    assert calls["init"] == ("wiimote-serial-bridge", True)
    assert calls["auth"] == ("u", "p")
    assert calls["connect"] == ("broker.local", 2883, 60)
    assert calls["loop_start"] is True


def test_mqtt_publish_waits_for_publish(monkeypatch):
    calls = {}

    class FakeResult:
        def wait_for_publish(self):
            calls["wait"] = True

    class FakeClient:
        def publish(self, topic, payload, retain=False):
            calls["publish"] = (topic, payload, retain)
            return FakeResult()

    mqtt_client.mqtt_publish(FakeClient(), "topic/x", "ON", retain=True)

    assert calls["publish"] == ("topic/x", "ON", True)
    assert calls["wait"] is True
