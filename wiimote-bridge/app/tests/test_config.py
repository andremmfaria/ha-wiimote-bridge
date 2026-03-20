from wiimote_bridge.utils.config import load_settings


def test_load_settings_from_environment(monkeypatch):
    monkeypatch.setenv(
        "RADIOS",
        '[{"port":"/dev/ttyACM0","baud":9600,"controller_id":4}]',
    )
    monkeypatch.setenv("MQTT_HOST", "broker.local")
    monkeypatch.setenv("MQTT_PORT", "2883")
    monkeypatch.setenv("MQTT_USERNAME", "user")
    monkeypatch.setenv("MQTT_PASSWORD", "secret")
    monkeypatch.setenv("MQTT_TRANSPORT", "websockets")
    monkeypatch.setenv("MQTT_SSL", "true")
    monkeypatch.setenv("MQTT_SSL_INSECURE", "true")
    monkeypatch.setenv("TOPIC_PREFIX", "wm")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DISCOVER_ENABLED", "false")

    settings = load_settings()

    assert len(settings.radios) == 1
    assert settings.radios[0].port == "/dev/ttyACM0"
    assert settings.radios[0].baud == 9600
    assert settings.radios[0].controller_id == 4
    assert settings.mqtt_host == "broker.local"
    assert settings.mqtt_port == 2883
    assert settings.mqtt_username == "user"
    assert settings.mqtt_password == "secret"
    assert settings.mqtt_transport == "websockets"
    assert settings.mqtt_ssl is True
    assert settings.mqtt_ssl_insecure is True
    assert settings.topic_prefix == "wm"
    assert settings.log_level == "debug"
    assert settings.discover_enabled is False


def test_load_settings_multiple_radios(monkeypatch):
    monkeypatch.setenv(
        "RADIOS",
        '[{"port":"/dev/ttyUSB0","baud":115200,"controller_id":1},{"port":"/dev/ttyUSB1","baud":115200,"controller_id":2}]',
    )

    settings = load_settings()

    assert len(settings.radios) == 2
    assert settings.radios[0].port == "/dev/ttyUSB0"
    assert settings.radios[0].controller_id == 1
    assert settings.radios[1].port == "/dev/ttyUSB1"
    assert settings.radios[1].controller_id == 2
    assert settings.discover_enabled is True
    assert settings.mqtt_transport == "tcp"
    assert settings.mqtt_ssl is False
    assert settings.mqtt_ssl_insecure is False


def test_load_settings_invalid_transport_falls_back_to_tcp(monkeypatch):
    monkeypatch.setenv("MQTT_TRANSPORT", "bad-value")

    settings = load_settings()

    assert settings.mqtt_transport == "tcp"


def test_load_settings_default_port_tcp_without_tls(monkeypatch):
    monkeypatch.setenv("MQTT_TRANSPORT", "tcp")
    monkeypatch.setenv("MQTT_SSL", "false")
    monkeypatch.setenv("MQTT_PORT", "0")

    settings = load_settings()

    assert settings.mqtt_port == 1883


def test_load_settings_default_port_tcp_with_tls(monkeypatch):
    monkeypatch.setenv("MQTT_TRANSPORT", "tcp")
    monkeypatch.setenv("MQTT_SSL", "true")
    monkeypatch.setenv("MQTT_PORT", "0")

    settings = load_settings()

    assert settings.mqtt_port == 8883


def test_load_settings_default_port_websocket_without_tls(monkeypatch):
    monkeypatch.setenv("MQTT_TRANSPORT", "websockets")
    monkeypatch.setenv("MQTT_SSL", "false")
    monkeypatch.setenv("MQTT_PORT", "0")

    settings = load_settings()

    assert settings.mqtt_port == 1884


def test_load_settings_default_port_websocket_with_tls(monkeypatch):
    monkeypatch.setenv("MQTT_TRANSPORT", "websockets")
    monkeypatch.setenv("MQTT_SSL", "true")
    monkeypatch.setenv("MQTT_PORT", "0")

    settings = load_settings()

    assert settings.mqtt_port == 8884


def test_load_settings_accepts_single_radio_object(monkeypatch):
    monkeypatch.setenv(
        "RADIOS",
        '{"port":"/dev/ttyUSB0","baud":115200,"controller_id":3}',
    )

    settings = load_settings()

    assert len(settings.radios) == 1
    assert settings.radios[0].controller_id == 3


def test_load_settings_accepts_double_encoded_radios_json(monkeypatch):
    monkeypatch.setenv(
        "RADIOS",
        '"[{\\"port\\":\\"/dev/ttyUSB0\\",\\"baud\\":115200,\\"controller_id\\":5}]"',
    )

    settings = load_settings()

    assert len(settings.radios) == 1
    assert settings.radios[0].controller_id == 5


def test_load_settings_health_port_from_environment(monkeypatch):
    monkeypatch.setenv("HEALTH_PORT", "9000")

    settings = load_settings()

    assert settings.health_port == 9000


def test_load_settings_invalid_health_port_disables_endpoint(monkeypatch):
    monkeypatch.setenv("HEALTH_PORT", "invalid")

    settings = load_settings()

    assert settings.health_port == 0
