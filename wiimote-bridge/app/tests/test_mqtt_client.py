from wiimote_bridge.transport import mqtt_client
from wiimote_bridge.utils.config import RadioConfig, Settings


def _patch_publish(monkeypatch):
    """Patch mqtt_publish to capture the single (topic, payload, retain) call."""
    called = {}

    def fake_publish(_client, topic, payload, retain=False):
        called["data"] = (topic, payload, retain)

    monkeypatch.setattr(mqtt_client, "mqtt_publish", fake_publish)
    return called


def test_publish_button_formats_topic_and_payload(monkeypatch):
    called = _patch_publish(monkeypatch)

    mqtt_client.publish_button(object(), "wiimote", 1, "A", True)

    assert called["data"] == ("wiimote/1/button/A", "ON", False)


def test_publish_connected_retained(monkeypatch):
    called = _patch_publish(monkeypatch)

    mqtt_client.publish_connected(object(), "wiimote", 1, False)

    assert called["data"] == ("wiimote/1/status/connected", "false", True)


def test_publish_battery_retained(monkeypatch):
    called = _patch_publish(monkeypatch)

    mqtt_client.publish_battery(object(), "wiimote", 2, 87)

    assert called["data"] == ("wiimote/2/status/battery", "87", True)


def test_publish_event_message_for_wiimote(monkeypatch):
    called = _patch_publish(monkeypatch)

    mqtt_client.publish_event_message(object(), "wiimote", 1, {"type": "status", "wiimote": 1, "waiting": True})

    assert called["data"] == (
        "wiimote/1/events/status",
        '{"type":"status","wiimote":1,"waiting":true}',
        False,
    )


def test_publish_event_message_for_wiimote_normalizes_fixed_id(monkeypatch):
    called = _patch_publish(monkeypatch)

    mqtt_client.publish_event_message(object(), "wiimote", 4, {"type": "status", "wiimote": 9, "waiting": True})

    assert called["data"] == (
        "wiimote/4/events/status",
        '{"type":"status","wiimote":4,"waiting":true}',
        False,
    )


def test_publish_event_message_for_device(monkeypatch):
    called = _patch_publish(monkeypatch)

    mqtt_client.publish_event_message(object(), "wiimote", 6, {"type": "status", "device": "esp32", "ready": True})

    assert called["data"] == (
        "wiimote/device/esp32/events/status",
        '{"type":"status","device":"esp32","ready":true}',
        False,
    )


def test_publish_heartbeat_normalizes_wiimote_id(monkeypatch):
    called = _patch_publish(monkeypatch)

    mqtt_client.publish_heartbeat(
        object(),
        "wiimote",
        3,
        {"type": "heartbeat", "device": "esp32", "wiimote": 1, "connected": True},
    )

    assert called["data"] == (
        "wiimote/3/status/heartbeat",
        '{"type":"heartbeat","device":"esp32","wiimote":3,"connected":true}',
        False,
    )


def test_publish_discovery_configs_publishes_connected_battery_and_buttons(monkeypatch):
    published = []

    def fake_publish(client, topic, payload, retain=False):
        published.append((topic, payload, retain))
        return True

    monkeypatch.setattr(mqtt_client, "mqtt_publish", fake_publish)

    result = mqtt_client.publish_discovery_configs(object(), "wiimote", [7])

    # 1 connected + 1 battery + 11 button entities
    assert len(published) == 13
    assert result == {"controllers": 1, "entities": 13, "failed": 0}
    assert published[0][0] == "homeassistant/binary_sensor/wiimote_7/connected/config"
    assert published[0][2] is True
    assert '"state_topic":"wiimote/7/status/connected"' in published[0][1]
    assert '"via_device"' not in published[0][1]

    battery_entry = next(x for x in published if x[0] == "homeassistant/sensor/wiimote_7/battery/config")
    assert battery_entry[2] is True
    assert '"state_topic":"wiimote/7/status/battery"' in battery_entry[1]

    button_entry = next(
        x for x in published if x[0] == "homeassistant/binary_sensor/wiimote_7/button_a/config"
    )
    assert button_entry[2] is True
    assert '"state_topic":"wiimote/7/button/A"' in button_entry[1]


def test_publish_discovery_configs_respects_custom_discovery_prefix(monkeypatch):
    published = []

    def fake_publish(client, topic, payload, retain=False):
        published.append((topic, payload, retain))
        return True

    monkeypatch.setattr(mqtt_client, "mqtt_publish", fake_publish)

    result = mqtt_client.publish_discovery_configs(object(), "wiimote", [1], discovery_prefix="ha")

    assert published[0][0].startswith("ha/")
    assert result["entities"] == 13


def test_publish_discovery_configs_counts_failures(monkeypatch):
    def fake_publish(client, topic, payload, retain=False):
        return not topic.endswith("button_a/config")

    monkeypatch.setattr(mqtt_client, "mqtt_publish", fake_publish)

    result = mqtt_client.publish_discovery_configs(object(), "wiimote", [1])

    assert result == {"controllers": 1, "entities": 12, "failed": 1}


def test_connect_mqtt_with_discovery_sets_auth_and_starts_loop(monkeypatch):
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
        radios=(RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=1),),
        discover_enabled=True,
        mqtt_host="broker.local",
        mqtt_port=2883,
        mqtt_username="u",
        mqtt_password="p",
        topic_prefix="wiimote",
    )

    client = mqtt_client.connect_mqtt_with_discovery(
        settings,
        discovery_enabled=True,
        discovery_topic_prefix="wiimote",
        discovery_wiimote_ids=(1,),
    )

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
        radios=(RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=1),),
        discover_enabled=True,
        mqtt_host="broker.local",
        mqtt_port=1883,
        mqtt_username="",
        mqtt_password="",
        topic_prefix="wiimote",
    )

    client = mqtt_client.connect_mqtt_with_discovery(
        settings,
        discovery_enabled=False,
        discovery_topic_prefix="wiimote",
        discovery_wiimote_ids=(),
    )

    # Paho v2 callback shape: (client, userdata, disconnect_flags, reason_code, properties)
    client.on_disconnect(client, None, None, 1, None)


def test_connect_mqtt_on_connect_publishes_discovery(monkeypatch):
    called = {}

    class FakeClient:
        def __init__(self, callback_api_version, client_id, clean_session):
            self.on_connect = None
            self.on_disconnect = None

        def connect(self, host, port, keepalive):
            return None

        def loop_start(self):
            return None

    monkeypatch.setattr(mqtt_client.mqtt, "Client", FakeClient)

    def fake_publish_discovery(client, topic_prefix, wiimote_ids, discovery_prefix="homeassistant"):
        called["args"] = (topic_prefix, tuple(wiimote_ids), discovery_prefix)
        return {"controllers": 2, "entities": 26, "failed": 0}

    monkeypatch.setattr(mqtt_client, "publish_discovery_configs", fake_publish_discovery)

    settings = Settings(
        radios=(RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=1),),
        discover_enabled=True,
        mqtt_host="broker.local",
        mqtt_port=1883,
        mqtt_username="",
        mqtt_password="",
        topic_prefix="wiimote",
    )

    client = mqtt_client.connect_mqtt_with_discovery(
        settings,
        discovery_enabled=True,
        discovery_topic_prefix="wiimote",
        discovery_wiimote_ids=(1, 9),
    )

    client.on_connect(client, None, None, 0, None)

    assert called["args"] == ("wiimote", (1, 9), "homeassistant")


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
