from wiimote_bridge.transport import serial_reader
from wiimote_bridge.utils.config import Settings


def test_open_serial_uses_settings(monkeypatch):
    called = {}

    def fake_serial_ctor(port, baud, timeout):
        called["args"] = (port, baud, timeout)
        return object()

    monkeypatch.setattr(serial_reader.serial, "Serial", fake_serial_ctor)

    settings = Settings(
        serial_port="/dev/ttyUSB1",
        serial_baud=57600,
        mqtt_host="host",
        mqtt_port=1883,
        mqtt_username="",
        mqtt_password="",
        topic_prefix="wiimote",
    )

    result = serial_reader.open_serial(settings)

    assert result is not None
    assert called["args"] == ("/dev/ttyUSB1", 57600, 1)
