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


def test_publish_battery_retained(monkeypatch):
    called = {}

    def fake_publish(client, topic, payload, retain=False):
        called["data"] = (topic, payload, retain)

    monkeypatch.setattr(mqtt_client, "mqtt_publish", fake_publish)

    mqtt_client.publish_battery(object(), "wiimote", 2, 87)

    assert called["data"] == ("wiimote/2/status/battery", "87", True)


def test_publish_event_message_for_wiimote(monkeypatch):
    called = {}

    def fake_publish(client, topic, payload, retain=False):
        called["data"] = (topic, payload, retain)

    monkeypatch.setattr(mqtt_client, "mqtt_publish", fake_publish)

    mqtt_client.publish_event_message(object(), "wiimote", {"type": "status", "wiimote": 1, "waiting": True})

    assert called["data"] == (
        "wiimote/1/events/status",
        '{"type":"status","wiimote":1,"waiting":true}',
        False,
    )
def test_publish_event_message_for_device(monkeypatch):
    called = {}

    def fake_publish(client, topic, payload, retain=False):
        called["data"] = (topic, payload, retain)

    monkeypatch.setattr(mqtt_client, "mqtt_publish", fake_publish)

    mqtt_client.publish_event_message(object(), "wiimote", {"type": "status", "device": "esp32", "ready": True})

    assert called["data"] == (
        "wiimote/device/esp32/events/status",
        '{"type":"status","device":"esp32","ready":true}',
        False,
    )


def test_connect_mqtt_sets_auth_and_starts_loop(monkeypatch):
    calls = {}

    class FakeClient:
        def __init__(self, callback_api_version, client_id, clean_session):
            calls["init"] = (callback_api_version, client_id, clean_session)
            self.on_connect = None
            self.on_disconnect = None

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
    assert calls["init"] == (
        mqtt_client.mqtt.CallbackAPIVersion.VERSION2,
        "wiimote-serial-bridge",
        True,
    )
    assert calls["auth"] == ("u", "p")
    assert calls["connect"] == ("broker.local", 2883, 60)
    assert calls["loop_start"] is True
    assert callable(client.on_connect)
    assert callable(client.on_disconnect)


def test_connect_mqtt_on_disconnect_accepts_v2_signature(monkeypatch):
    class FakeClient:
        def __init__(self, callback_api_version, client_id, clean_session):
            self.on_connect = None
            self.on_disconnect = None

        def connect(self, host, port, keepalive):
            return None

        def loop_start(self):
            return None

    monkeypatch.setattr(mqtt_client.mqtt, "Client", FakeClient)

    settings = Settings(
        serial_port="/dev/ttyUSB0",
        serial_baud=115200,
        mqtt_host="broker.local",
        mqtt_port=1883,
        mqtt_username="",
        mqtt_password="",
        topic_prefix="wiimote",
    )

    client = mqtt_client.connect_mqtt(settings)

    # Paho v2 callback shape: (client, userdata, disconnect_flags, reason_code, properties)
    client.on_disconnect(client, None, None, 1, None)


def test_mqtt_publish_waits_for_publish(monkeypatch):
    calls = {}

    class FakeResult:
        rc = mqtt_client.mqtt.MQTT_ERR_SUCCESS

        def wait_for_publish(self):
            calls["wait"] = True

    class FakeClient:
        def is_connected(self):
            return True

        def publish(self, topic, payload, retain=False):
            calls["publish"] = (topic, payload, retain)
            return FakeResult()

    mqtt_client.mqtt_publish(FakeClient(), "topic/x", "ON", retain=True)

    assert calls["publish"] == ("topic/x", "ON", True)
    assert calls["wait"] is True


def test_mqtt_publish_skips_when_client_is_disconnected():
    calls = {}

    class FakeClient:
        def is_connected(self):
            return False

        def publish(self, topic, payload, retain=False):
            calls["publish"] = (topic, payload, retain)
            raise AssertionError("publish should not be called while disconnected")

    published = mqtt_client.mqtt_publish(FakeClient(), "topic/x", "ON", retain=True)

    assert published is False
    assert "publish" not in calls


def test_mqtt_publish_skips_runtime_publish_failure():
    calls = {}

    class FakeResult:
        rc = mqtt_client.mqtt.MQTT_ERR_SUCCESS

        def wait_for_publish(self):
            calls["wait"] = True
            raise RuntimeError("Message publish failed: The client is not currently connected.")

    class FakeClient:
        def is_connected(self):
            return True

        def publish(self, topic, payload, retain=False):
            calls["publish"] = (topic, payload, retain)
            return FakeResult()

    published = mqtt_client.mqtt_publish(FakeClient(), "topic/x", "ON", retain=True)

    assert published is False
    assert calls["publish"] == ("topic/x", "ON", True)
    assert calls["wait"] is True


def test_mqtt_publish_warning_is_rate_limited(monkeypatch):
    warnings = []

    class FakeLogger:
        def warning(self, message, *args):
            if args:
                warnings.append(message % args)
                return
            warnings.append(message)

    ticks = iter([100.0, 105.0, 116.0])
    monkeypatch.setattr(mqtt_client.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(mqtt_client, "LOGGER", FakeLogger())
    monkeypatch.setattr(mqtt_client, "_last_publish_warning_at", None)

    class FakeClient:
        def is_connected(self):
            return False

        def publish(self, topic, payload, retain=False):
            raise AssertionError("publish should not be called while disconnected")

    mqtt_client.mqtt_publish(FakeClient(), "topic/1", "ON")
    mqtt_client.mqtt_publish(FakeClient(), "topic/2", "ON")
    mqtt_client.mqtt_publish(FakeClient(), "topic/3", "ON")

    assert warnings == [
        "Skipping MQTT publish while client is disconnected: topic/1",
        "Skipping MQTT publish while client is disconnected: topic/3",
    ]
