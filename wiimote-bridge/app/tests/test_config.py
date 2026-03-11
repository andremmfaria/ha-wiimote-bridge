from wiimote_bridge.utils.config import load_settings


def test_load_settings_from_environment(monkeypatch):
    monkeypatch.setenv("SERIAL_PORT", "/dev/ttyACM0")
    monkeypatch.setenv("SERIAL_BAUD", "9600")
    monkeypatch.setenv("MQTT_HOST", "broker.local")
    monkeypatch.setenv("MQTT_PORT", "2883")
    monkeypatch.setenv("MQTT_USERNAME", "user")
    monkeypatch.setenv("MQTT_PASSWORD", "secret")
    monkeypatch.setenv("TOPIC_PREFIX", "wm")

    settings = load_settings()

    assert settings.serial_port == "/dev/ttyACM0"
    assert settings.serial_baud == 9600
    assert settings.mqtt_host == "broker.local"
    assert settings.mqtt_port == 2883
    assert settings.mqtt_username == "user"
    assert settings.mqtt_password == "secret"
    assert settings.topic_prefix == "wm"
