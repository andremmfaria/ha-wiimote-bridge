# Home Assistant WiiMote Bridge

Use a Nintendo Wii Remote as a Home Assistant controller.

This project connects a Wii Remote to an ESP32 over Bluetooth and exposes button presses to Home Assistant via MQTT using a USB serial bridge.

## Architecture

```text
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

The add-on is packaged as a Home Assistant custom repository and publishes pre-built multi-architecture container images to GHCR for tagged releases.

## Features

- Uses inexpensive ESP32 hardware
- No WiFi required for the ESP32
- USB serial connection to Home Assistant host
- MQTT interface compatible with many systems
- Clean JSON protocol between firmware and HA
- Works with standard Wii Remotes
- Dedicated MQTT topics for button, connection, heartbeat, and battery
- Passthrough MQTT events topics for all valid firmware JSON messages

## Repository Structure

```text
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
        ├── pyproject.toml
        ├── uv.lock
        └── src/
            └── wiimote_bridge/
                ├── core/
                ├── transport/
                └── utils/
```

## Quick Start

1. Flash the ESP32 firmware  
   → see [docs/firmware-setup.md](docs/firmware-setup.md) or `esp32/README.md`

2. Connect the ESP32 to the Home Assistant host via USB.

3. Install the **WiiMote Bridge** add-on from this repository.

4. Configure the add-on:

```yaml
radios:
  - port: /dev/ttyUSB0
    baud: 115200
    controller_id: 1
mqtt_host: core-mosquitto
mqtt_port: 1883
topic_prefix: wiimote
```

Each entry in `radios` defines one ESP32 radio. Add more entries for each additional ESP32 connected to the host.

Then:

1. Start the add-on.

2. Pair the Wii Remote by pressing **1 + 2**.

3. Button events will appear in MQTT topics such as:

```text
wiimote/1/button/A
wiimote/1/button/B
wiimote/1/button/PLUS
wiimote/1/status/connected
wiimote/1/status/heartbeat
wiimote/1/status/battery
wiimote/1/events/status
```

Payloads:

```text
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

- ESP32-WROOM-32 development boards
- Nintendo Wii Remote (standard)

Other ESP32 boards should work as long as they support **Bluetooth Classic**.

## Known Limitations

- No accelerometer or nunchuk MQTT topics yet
- No command channel from Home Assistant back to firmware yet
- Motion / accelerometer support will be added later
- Each ESP32 radio can pair with only one Wii Remote when using ESP32Wiimote
- To use multiple Wii Remotes, connect multiple ESP32 radios and add one entry per radio to `radios` in the single add-on instance

## Why This Exists

Home Assistant does not natively support Wii Remotes.
While they are old gaming controllers, they make excellent wireless remotes for home automation projects.

This project repurposes them using inexpensive ESP32 hardware.

## Future Improvements

- accelerometer support
- rumble control from Home Assistant
- LED control
- MQTT auto-discovery

## Release Process

The Home Assistant add-on is released from Git tags.

1. Update `wiimote-bridge/config.yaml` with the new add-on version.
2. Update `wiimote-bridge/CHANGELOG.md`.
3. If Python dependencies changed, regenerate `wiimote-bridge/app/uv.lock`.
4. Create and push a matching tag such as `v0.1.0`.

The tag triggers GitHub Actions to:

- validate the tag matches the add-on version
- build architecture-specific images for Home Assistant
- publish them to GHCR
- create a GitHub release

## License

MIT
