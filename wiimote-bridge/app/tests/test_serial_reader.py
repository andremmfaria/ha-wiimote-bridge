from wiimote_bridge.transport import serial_reader


def test_open_serial_uses_port_and_baud(monkeypatch):
    called = {}

    def fake_serial_ctor(port, baud, timeout):
        called["args"] = (port, baud, timeout)
        return object()

    monkeypatch.setattr(serial_reader.serial, "Serial", fake_serial_ctor)

    result = serial_reader.open_serial("/dev/ttyUSB1", 57600)

    assert result is not None
    assert called["args"] == ("/dev/ttyUSB1", 57600, 1)
