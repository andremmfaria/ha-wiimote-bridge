# ESP32 Firmware

This directory contains the firmware that connects a Nintendo Wii Remote to an ESP32 and exposes button events over USB serial.

The firmware acts as the Bluetooth bridge for the project.

## Hardware

Tested with:

- ESP32-WROOM-32 development board
- USB connection to the Home Assistant host

The ESP32 must support **Bluetooth Classic** (not only BLE).

## Requirements

- Arduino ESP32 Core **2.0.17**
- `ESP32Wiimote` library by hrgraf
- `arduino-cli` or Arduino IDE

⚠️ ESP32 Arduino Core **3.x does not work** with the Wiimote library.

Symptoms:

```
btStart() failed
```

If you see this error, downgrade to core `2.0.17`.

## Installing the ESP32 Core

Using `arduino-cli`:

```
arduino-cli core install esp32:esp32@2.0.17
```

Verify installation:

```
arduino-cli core list
```

## Installing the Wiimote Library

Install directly from GitHub:

```
arduino-cli lib install --git-url [https://github.com/hrgraf/ESP32Wiimote](https://github.com/hrgraf/ESP32Wiimote)
```

## Firmware Location

```
esp32/
    └── wiimote_serial_bridge/
        └── wiimote_serial_bridge.ino
```

## Compile

From the firmware directory:

```
arduino-cli compile --fqbn esp32:esp32:esp32 .
```

## Upload

Connect the ESP32 via USB and run:

```
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 .
```

Replace `/dev/ttyUSB0` with your serial device if necessary.

## Pairing the Wii Remote

1. Power the ESP32
2. Open the serial monitor
3. Press **1 + 2** on the Wii Remote

Once connected, you should see:

```
{"type":"status","wiimote":1,"connected":true}
```

## Serial Output Format

The firmware emits JSON lines over serial.

Example:

```
{"type":"status","device":"esp32","ready":true}
{"type":"status","wiimote":1,"connected":true}
{"type":"btn","wiimote":1,"btn":"A","down":true}
{"type":"btn","wiimote":1,"btn":"A","down":false}
```

These messages are consumed by the Home Assistant add-on and converted to MQTT topics.

## Heartbeat

Every 10 seconds the firmware emits:

```
{"type":"heartbeat","device":"esp32","wiimote":1,"connected":true}
```

This allows the Home Assistant bridge to detect stale connections.

## Button Mapping

Supported buttons:

```
A
B
ONE
TWO
PLUS
MINUS
HOME
UP
DOWN
LEFT
RIGHT
```

## Example Serial Monitor

```
{"type":"status","wiimote":1,"connected":true}
{"type":"btn","wiimote":1,"btn":"A","down":true}
{"type":"btn","wiimote":1,"btn":"A","down":false}
{"type":"btn","wiimote":1,"btn":"PLUS","down":true}
{"type":"btn","wiimote":1,"btn":"PLUS","down":false}
```

## Future Firmware Features

Planned improvements:

- accelerometer events
- rumble control
- LED control
- multiple Wiimotes
