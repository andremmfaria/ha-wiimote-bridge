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

