import socket
import ssl
import threading

import pytest

import wiimote_bridge.transport.mqtt.connection as connection
import wiimote_bridge.transport.mqtt.discovery as discovery
import wiimote_bridge.transport.mqtt.errors as errors
import wiimote_bridge.transport.mqtt.publish as publish
from wiimote_bridge.utils.config import RadioConfig, Settings


def _patch_publish(monkeypatch):
    """Patch message to capture the single (topic, payload, retain) call."""
    called = {}

    def fake_publish(_client, topic, payload, retain=False):
        called["data"] = (topic, payload, retain)

    monkeypatch.setattr(publish, "message", fake_publish)
    return called


def test_publish_button_formats_topic_and_payload(monkeypatch):
    called = _patch_publish(monkeypatch)

    publish.button(object(), "wiimote", 1, "A", True)

    assert called["data"] == ("wiimote/1/button/A", "ON", False)


def test_publish_connected_retained(monkeypatch):
    called = _patch_publish(monkeypatch)

    publish.connected(object(), "wiimote", 1, False)

    assert called["data"] == ("wiimote/1/status/connected", "false", True)


def test_publish_battery_retained(monkeypatch):
    called = _patch_publish(monkeypatch)

    publish.battery(object(), "wiimote", 2, 87)

    assert called["data"] == ("wiimote/2/status/battery", "87", True)


def test_publish_event_message_for_wiimote(monkeypatch):
    called = _patch_publish(monkeypatch)

    publish.event_message(
        object(), "wiimote", 1, {"type": "status", "wiimote": 1, "waiting": True}
    )

    assert called["data"] == (
        "wiimote/1/events/status",
        '{"type":"status","wiimote":1,"waiting":true}',
        False,
    )


def test_publish_event_message_for_wiimote_normalizes_fixed_id(monkeypatch):
    called = _patch_publish(monkeypatch)

    publish.event_message(
        object(), "wiimote", 4, {"type": "status", "wiimote": 9, "waiting": True}
    )

    assert called["data"] == (
        "wiimote/4/events/status",
        '{"type":"status","wiimote":4,"waiting":true}',
        False,
    )


def test_publish_event_message_for_device(monkeypatch):
    called = _patch_publish(monkeypatch)

    publish.event_message(
        object(), "wiimote", 6, {"type": "status", "device": "esp32", "ready": True}
    )

    assert called["data"] == (
        "wiimote/device/esp32/events/status",
        '{"type":"status","device":"esp32","ready":true}',
        False,
    )


def test_publish_heartbeat_normalizes_wiimote_id(monkeypatch):
    called = _patch_publish(monkeypatch)

    publish.heartbeat(
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

    monkeypatch.setattr(discovery, "message", fake_publish)

    result = discovery.configs(object(), "wiimote", [7])

    # 1 connected + 1 battery + 11 button entities
    assert len(published) == 13
    assert result == {"controllers": 1, "entities": 13, "failed": 0}
    assert published[0][0] == "homeassistant/binary_sensor/wiimote_7/connected/config"
    assert published[0][2] is True
    assert '"state_topic":"wiimote/7/status/connected"' in published[0][1]
    assert '"via_device"' not in published[0][1]

    battery_entry = next(
        x for x in published if x[0] == "homeassistant/sensor/wiimote_7/battery/config"
    )
    assert battery_entry[2] is True
    assert '"state_topic":"wiimote/7/status/battery"' in battery_entry[1]

    button_entry = next(
        x
        for x in published
        if x[0] == "homeassistant/binary_sensor/wiimote_7/button_a/config"
    )
    assert button_entry[2] is True
    assert '"state_topic":"wiimote/7/button/A"' in button_entry[1]


def test_publish_discovery_configs_respects_custom_discovery_prefix(monkeypatch):
    published = []

    def fake_publish(client, topic, payload, retain=False):
        published.append((topic, payload, retain))
        return True

    monkeypatch.setattr(discovery, "message", fake_publish)

    result = discovery.configs(object(), "wiimote", [1], discovery_prefix="ha")

    assert published[0][0].startswith("ha/")
    assert result["entities"] == 13


def test_publish_discovery_configs_counts_failures(monkeypatch):
    def fake_publish(client, topic, payload, retain=False):
        return not topic.endswith("button_a/config")

    monkeypatch.setattr(discovery, "message", fake_publish)

    result = discovery.configs(object(), "wiimote", [1])

    assert result == {"controllers": 1, "entities": 12, "failed": 1}


def test_connect_mqtt_with_discovery_sets_auth_and_starts_loop(monkeypatch):
    calls = {}

    class FakeClient:
        def __init__(self, callback_api_version, client_id, clean_session, transport):
            calls["init"] = (callback_api_version, client_id, clean_session, transport)
            self.on_connect = None
            self.on_disconnect = None

        def username_pw_set(self, username, password):
            calls["auth"] = (username, password)

        def connect(self, host, port, keepalive):
            calls["connect"] = (host, port, keepalive)

        def loop_start(self):
            calls["loop_start"] = True

    monkeypatch.setattr(connection.mqtt, "Client", FakeClient)

    settings = Settings(
        radios=(RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=1),),
        discover_enabled=True,
        mqtt_host="broker.local",
        mqtt_port=2883,
        mqtt_username="u",
        mqtt_password="p",
        topic_prefix="wiimote",
    )

    client = connection.connect_with_discovery(
        settings,
        discovery_enabled=True,
        discovery_topic_prefix="wiimote",
        discovery_wiimote_ids=(1,),
    )

    assert client is not None
    assert calls["init"] == (
        connection.mqtt.CallbackAPIVersion.VERSION2,
        "wiimote-serial-bridge",
        True,
        "tcp",
    )
    assert calls["auth"] == ("u", "p")
    assert calls["connect"] == ("broker.local", 2883, 60)
    assert calls["loop_start"] is True
    assert callable(client.on_connect)
    assert callable(client.on_disconnect)


def test_connect_mqtt_on_disconnect_accepts_v2_signature(monkeypatch):
    class FakeClient:
        def __init__(self, callback_api_version, client_id, clean_session, transport):
            self.on_connect = None
            self.on_disconnect = None

        def connect(self, host, port, keepalive):
            return None

        def loop_start(self):
            return None

    monkeypatch.setattr(connection.mqtt, "Client", FakeClient)

    settings = Settings(
        radios=(RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=1),),
        discover_enabled=True,
        mqtt_host="broker.local",
        mqtt_port=1883,
        mqtt_username="",
        mqtt_password="",
        topic_prefix="wiimote",
    )

    client = connection.connect_with_discovery(
        settings,
        discovery_enabled=False,
        discovery_topic_prefix="wiimote",
        discovery_wiimote_ids=(),
    )

    # Paho v2 callback shape: (client, userdata, disconnect_flags, reason_code, properties)
    client.on_disconnect(client, None, None, 1, None)


def test_connect_mqtt_logs_explicit_auth_failure_on_connect(monkeypatch, caplog):
    class FakeClient:
        def __init__(self, callback_api_version, client_id, clean_session, transport):
            self.on_connect = None
            self.on_disconnect = None

        def connect(self, host, port, keepalive):
            return None

        def loop_start(self):
            return None

    monkeypatch.setattr(connection.mqtt, "Client", FakeClient)

    settings = Settings(
        radios=(RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=1),),
        discover_enabled=True,
        mqtt_host="core-mosquitto",
        mqtt_port=1883,
        mqtt_username="",
        mqtt_password="",
        topic_prefix="wiimote",
    )

    client = connection.connect_with_discovery(
        settings,
        discovery_enabled=False,
        discovery_topic_prefix="wiimote",
        discovery_wiimote_ids=(),
    )

    with caplog.at_level("WARNING"):
        client.on_connect(client, None, None, 5, None)

    assert "MQTT connection failed:" in caplog.text
    assert "fill in mqtt.username and mqtt.password" in caplog.text


def test_connect_mqtt_logs_explicit_auth_failure_on_disconnect(monkeypatch, caplog):
    class FakeClient:
        def __init__(self, callback_api_version, client_id, clean_session, transport):
            self.on_connect = None
            self.on_disconnect = None

        def username_pw_set(self, username, password):
            return None

        def connect(self, host, port, keepalive):
            return None

        def loop_start(self):
            return None

    monkeypatch.setattr(connection.mqtt, "Client", FakeClient)
    monkeypatch.setattr(
        errors.mqtt,
        "convert_disconnect_error_code_to_reason_code",
        lambda reason_code: "Not authorized",
    )

    settings = Settings(
        radios=(RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=1),),
        discover_enabled=True,
        mqtt_host="core-mosquitto",
        mqtt_port=1883,
        mqtt_username="user",
        mqtt_password="bad-password",
        topic_prefix="wiimote",
    )

    client = connection.connect_with_discovery(
        settings,
        discovery_enabled=False,
        discovery_topic_prefix="wiimote",
        discovery_wiimote_ids=(),
    )

    with caplog.at_level("WARNING"):
        client.on_disconnect(client, None, None, 7, None)

    assert "MQTT client disconnected:" in caplog.text
    assert "Check mqtt.username and mqtt.password" in caplog.text


def test_connect_mqtt_logs_hostname_resolution_failure(monkeypatch, caplog):
    class FakeClient:
        def __init__(self, callback_api_version, client_id, clean_session, transport):
            self.on_connect = None
            self.on_disconnect = None

        def connect(self, host, port, keepalive):
            raise socket.gaierror("Name or service not known")

        def loop_start(self):
            raise AssertionError("loop_start should not be called when connect fails")

    monkeypatch.setattr(connection.mqtt, "Client", FakeClient)

    settings = Settings(
        radios=(RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=1),),
        discover_enabled=True,
        mqtt_host="missing-broker",
        mqtt_port=1883,
        mqtt_username="",
        mqtt_password="",
        topic_prefix="wiimote",
    )

    with caplog.at_level("WARNING"):
        with pytest.raises(socket.gaierror):
            connection.connect_with_discovery(
                settings,
                discovery_enabled=False,
                discovery_topic_prefix="wiimote",
                discovery_wiimote_ids=(),
            )

    assert "MQTT initial connect failed:" in caplog.text
    assert "Name resolution failed for MQTT host missing-broker" in caplog.text
    assert "ensure the broker hostname is resolvable" in caplog.text


def test_connect_mqtt_logs_tls_failure(monkeypatch, caplog):
    class FakeClient:
        def __init__(self, callback_api_version, client_id, clean_session, transport):
            self.on_connect = None
            self.on_disconnect = None

        def connect(self, host, port, keepalive):
            raise ssl.SSLError("CERTIFICATE_VERIFY_FAILED")

        def loop_start(self):
            raise AssertionError("loop_start should not be called when connect fails")

        def tls_set(self, cert_reqs=None):
            return None

        def tls_insecure_set(self, value):
            return None

    monkeypatch.setattr(connection.mqtt, "Client", FakeClient)

    settings = Settings(
        radios=(RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=1),),
        discover_enabled=True,
        mqtt_host="core-mosquitto",
        mqtt_port=8883,
        mqtt_username="",
        mqtt_password="",
        topic_prefix="wiimote",
        mqtt_ssl=True,
    )

    with caplog.at_level("WARNING"):
        with pytest.raises(ssl.SSLError):
            connection.connect_with_discovery(
                settings,
                discovery_enabled=False,
                discovery_topic_prefix="wiimote",
                discovery_wiimote_ids=(),
            )

    assert "MQTT initial connect failed:" in caplog.text
    assert "TLS handshake failed while connecting to MQTT broker" in caplog.text
    assert (
        "Check mqtt.ssl, mqtt.ssl_insecure, and the broker certificate configuration"
        in caplog.text
    )


def test_connect_mqtt_logs_connection_refused(monkeypatch, caplog):
    class FakeClient:
        def __init__(self, callback_api_version, client_id, clean_session, transport):
            self.on_connect = None
            self.on_disconnect = None

        def connect(self, host, port, keepalive):
            raise ConnectionRefusedError("Connection refused")

        def loop_start(self):
            raise AssertionError("loop_start should not be called when connect fails")

    monkeypatch.setattr(connection.mqtt, "Client", FakeClient)

    settings = Settings(
        radios=(RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=1),),
        discover_enabled=True,
        mqtt_host="core-mosquitto",
        mqtt_port=1883,
        mqtt_username="",
        mqtt_password="",
        topic_prefix="wiimote",
    )

    with caplog.at_level("WARNING"):
        with pytest.raises(ConnectionRefusedError):
            connection.connect_with_discovery(
                settings,
                discovery_enabled=False,
                discovery_topic_prefix="wiimote",
                discovery_wiimote_ids=(),
            )

    assert "MQTT initial connect failed:" in caplog.text
    assert "TCP connection refused by MQTT broker" in caplog.text
    assert (
        "Check mqtt.host, mqtt.port, and that the broker is running and reachable"
        in caplog.text
    )


def test_connect_mqtt_on_connect_publishes_discovery(monkeypatch):
    called = {}

    class FakeClient:
        def __init__(self, callback_api_version, client_id, clean_session, transport):
            self.on_connect = None
            self.on_disconnect = None

        def connect(self, host, port, keepalive):
            return None

        def loop_start(self):
            return None

    monkeypatch.setattr(connection.mqtt, "Client", FakeClient)

    done = threading.Event()

    def fake_publish_discovery(
        client, topic_prefix, wiimote_ids, discovery_prefix="homeassistant"
    ):
        called["args"] = (topic_prefix, tuple(wiimote_ids), discovery_prefix)
        done.set()
        return {"controllers": 2, "entities": 26, "failed": 0}

    monkeypatch.setattr(connection, "configs", fake_publish_discovery)

    settings = Settings(
        radios=(RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=1),),
        discover_enabled=True,
        mqtt_host="broker.local",
        mqtt_port=1883,
        mqtt_username="",
        mqtt_password="",
        topic_prefix="wiimote",
    )

    client = connection.connect_with_discovery(
        settings,
        discovery_enabled=True,
        discovery_topic_prefix="wiimote",
        discovery_wiimote_ids=(1, 9),
    )

    client.on_connect(client, None, None, 0, None)
    done.wait(timeout=2)

    assert called["args"] == ("wiimote", (1, 9), "homeassistant")


def test_connect_mqtt_with_ssl_and_insecure_cert_verification(monkeypatch):
    calls = {}

    class FakeClient:
        def __init__(self, callback_api_version, client_id, clean_session, transport):
            calls["init"] = (callback_api_version, client_id, clean_session, transport)
            self.on_connect = None
            self.on_disconnect = None

        def connect(self, host, port, keepalive):
            calls["connect"] = (host, port, keepalive)

        def loop_start(self):
            calls["loop_start"] = True

        def tls_set(self, cert_reqs=None):
            calls["tls_set"] = cert_reqs

        def tls_insecure_set(self, value):
            calls["tls_insecure_set"] = value

    monkeypatch.setattr(connection.mqtt, "Client", FakeClient)

    settings = Settings(
        radios=(RadioConfig(port="/dev/ttyUSB0", baud=115200, controller_id=1),),
        discover_enabled=True,
        mqtt_host="broker.local",
        mqtt_port=8883,
        mqtt_username="",
        mqtt_password="",
        topic_prefix="wiimote",
        mqtt_transport="websockets",
        mqtt_ssl=True,
        mqtt_ssl_insecure=True,
    )

    client = connection.connect_with_discovery(
        settings,
        discovery_enabled=False,
        discovery_topic_prefix="wiimote",
        discovery_wiimote_ids=(),
    )

    assert client is not None
    assert calls["init"][3] == "websockets"
    assert calls["tls_set"] == ssl.CERT_NONE
    assert calls["tls_insecure_set"] is True


def test_mqtt_publish_waits_for_publish(monkeypatch):
    calls = {}

    class FakeResult:
        rc = publish.mqtt.MQTT_ERR_SUCCESS

        def wait_for_publish(self):
            calls["wait"] = True

    class FakeClient:
        def is_connected(self):
            return True

        def publish(self, topic, payload, retain=False):
            calls["publish"] = (topic, payload, retain)
            return FakeResult()

    publish.message(FakeClient(), "topic/x", "ON", retain=True)

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

    published = publish.message(FakeClient(), "topic/x", "ON", retain=True)

    assert published is False
    assert "publish" not in calls


def test_mqtt_publish_skips_runtime_publish_failure():
    calls = {}

    class FakeResult:
        rc = publish.mqtt.MQTT_ERR_SUCCESS

        def wait_for_publish(self):
            calls["wait"] = True
            raise RuntimeError(
                "Message publish failed: The client is not currently connected."
            )

    class FakeClient:
        def is_connected(self):
            return True

        def publish(self, topic, payload, retain=False):
            calls["publish"] = (topic, payload, retain)
            return FakeResult()

    published = publish.message(FakeClient(), "topic/x", "ON", retain=True)

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
    monkeypatch.setattr(publish.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(publish, "LOGGER", FakeLogger())
    monkeypatch.setattr(publish, "_last_publish_warning_at", None)

    class FakeClient:
        def is_connected(self):
            return False

        def publish(self, topic, payload, retain=False):
            raise AssertionError("publish should not be called while disconnected")

    publish.message(FakeClient(), "topic/1", "ON")
    publish.message(FakeClient(), "topic/2", "ON")
    publish.message(FakeClient(), "topic/3", "ON")

    assert warnings == [
        "Skipping MQTT publish while client is disconnected: topic/1",
        "Skipping MQTT publish while client is disconnected: topic/3",
    ]
