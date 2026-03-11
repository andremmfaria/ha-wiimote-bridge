# Home Assistant WiiMote Bridge

Use a Nintendo Wii Remote as a Home Assistant controller.

This project connects a Wii Remote to an ESP32 over Bluetooth and exposes button presses to Home Assistant via MQTT using a USB serial bridge.

## Architecture

```
Wii Remote
↓ Bluetooth
ESP32
↓ USB Serial
Home Assistant Add-on
↓ MQTT
Home Assistant Automations
```

The ESP32 handles the Bluetooth stack and translates Wiimote events into a simple JSON protocol over USB serial.  
A Home Assistant add-on reads the serial stream and publishes MQTT topics that Home Assistant automations can use.

## Features

- Uses inexpensive ESP32 hardware
- No WiFi required for the ESP32
- USB serial connection to Home Assistant host
- MQTT interface compatible with many systems
- Clean JSON protocol between firmware and HA
- Works with standard Wii Remotes

## Repository Structure

```
ha-wiimote-bridge/
├── README.md
├── repository.yaml
├── docs/
│   ├── architecture.md
│   ├── protocol.md
│   ├── firmware-setup.md
│   └── ha-addon-setup.md
├── esp32/
│   ├── README.md
│   └── wiimote-serial-bridge/
│       ├── wiimote-serial-bridge.ino
│       ├── include/
│       │   ├── buttons.h
│       │   ├── messages.h
│       │   └── state.h
│       └── src/
│           ├── buttons.cpp
│           └── messages.cpp
└── wiimote-bridge/
    ├── config.yaml
    ├── Dockerfile
    ├── run.sh
    └── app/
        ├── requirements.txt
        └── main.py
```

## Quick Start

1. Flash the ESP32 firmware  
   → see [docs/firmware-setup.md](docs/firmware-setup.md) or `esp32/README.md`

2. Connect the ESP32 to the Home Assistant host via USB.

3. Install the **WiiMote Bridge** add-on from this repository.

4. Configure the add-on:

```yaml
serial_port: /dev/ttyUSB0
serial_baud: 115200
mqtt_host: core-mosquitto
mqtt_port: 1883
topic_prefix: wiimote
```

5. Start the add-on.

6. Pair the Wii Remote by pressing **1 + 2**.

7. Button events will appear in MQTT topics such as:

```
wiimote/1/button/A
wiimote/1/button/B
wiimote/1/button/PLUS
```

Payloads:

```
ON
OFF
```

## Example Home Assistant Automation

```yaml
alias: Toggle lights with Wii Remote A button
trigger:
  - platform: mqtt
    topic: wiimote/1/button/A
    payload: "ON"

action:
  - service: light.toggle
    target:
      entity_id: light.living_room
```

## Supported Hardware

Tested with:

* ESP32-WROOM-32 development boards
* Nintendo Wii Remote (standard)

Other ESP32 boards should work as long as they support **Bluetooth Classic**.

## Known Limitations

* Only button events are currently supported
* Motion / accelerometer support will be added later
* Only one Wii Remote supported in the current firmware

## Why This Exists

Home Assistant does not natively support Wii Remotes.
While they are old gaming controllers, they make excellent wireless remotes for home automation projects.

This project repurposes them using inexpensive ESP32 hardware.

## Future Improvements

* accelerometer support
* rumble control from Home Assistant
* LED control
* multiple Wii Remotes
* MQTT auto-discovery

## License

MIT
