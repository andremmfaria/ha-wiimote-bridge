# System Architecture

This project turns a Nintendo Wii Remote into a Home Assistant input device by splitting the problem into two separate runtime environments:

1. ESP32 firmware handles Bluetooth Classic communication with the controller.
2. A Home Assistant add-on handles serial input and MQTT publication.

That separation keeps Bluetooth and hardware handling out of Home Assistant itself and exposes a simple MQTT interface for automations.

## End-to-End Flow

```text
Wii Remote
  -> Bluetooth Classic HID
ESP32 firmware
  -> line-delimited JSON over USB serial
Home Assistant add-on
  -> MQTT topics
Home Assistant automations and other MQTT consumers
```

## Main Components

### Wii Remote

The Wii Remote is the user input device.

Hardware capabilities include:

- digital buttons
- accelerometer
- IR camera
- rumble motor
- LEDs

Current project usage focuses on button input. The rest of the hardware capabilities are not yet fully exposed through the bridge.

### ESP32 Firmware

The ESP32 acts as the Bluetooth host for the Wii Remote and as the serial producer for the rest of the system.

Its current responsibilities are:

- initialize the Bluetooth library
- prompt the user to pair with `1 + 2`
- maintain controller connection state
- emit line-delimited JSON messages over USB serial
- emit button press and release transitions
- emit periodic heartbeat messages
- emit battery updates when they change

Important implementation details:

- The firmware runs at `115200` baud.
- It configures `ESP32Wiimote` library logging at warning level.
- It captures the first button baseline after connection to avoid false button transitions.
- It emits heartbeat messages every 10 seconds.
- It requests battery updates every 60 seconds while connected.
- It emits periodic waiting messages every 5 seconds while not connected.

### USB Serial Link

The USB cable between the ESP32 and the Home Assistant host is the transport boundary between firmware and add-on.

On the host, this usually appears as a device such as:

- `/dev/ttyUSB0`
- `/dev/ttyUSB1`
- `/dev/ttyACM0`

The add-on does not speak Bluetooth directly. It only reads serial lines from this device.

### Home Assistant Add-on

The add-on is a Python application packaged as a Home Assistant add-on container.

Its responsibilities are:

- read add-on options from Home Assistant
- configure runtime logging
- connect to MQTT
- open the configured serial device
- decode incoming serial lines
- parse JSON objects
- forward every valid JSON message to MQTT events topics
- map supported message types into convenience MQTT topics
- recover from transient serial failures

The add-on currently handles these serial message types:

- `btn`
- `status` with `connected`
- `heartbeat`
- `battery`

Some firmware fields do not have a dedicated convenience topic yet, but are still available via events topics:

- `status` with `ready`
- `status` with `waiting`
- `status` with pairing notes

### MQTT Layer

MQTT is the stable integration surface for Home Assistant and other systems.

Published topics currently include:

- `wiimote/1/button/A`
- `wiimote/1/button/B`
- `wiimote/1/button/PLUS`
- `wiimote/1/status/connected`
- `wiimote/1/status/heartbeat`
- `wiimote/1/status/battery`
- `wiimote/1/events/status`
- `wiimote/device/esp32/events/status`

This makes the project usable not only from Home Assistant, but also from:

- Node-RED
- openHAB
- custom scripts
- MQTT inspection tools

### Home Assistant

Home Assistant consumes the MQTT topics with automations, scripts, dashboards, or external integrations.

Typical usage patterns are:

- button press triggers for lights and scenes
- connection-state notifications
- heartbeat monitoring for device health

## Protocol Boundary

The serial protocol is intentionally simple and line-oriented.

Example button message from the firmware:

```json
{"type":"btn","wiimote":1,"btn":"A","down":true}
```

Current MQTT translation by the add-on:

```text
topic: wiimote/1/button/A
payload: ON
```

Example connection message from the firmware:

```json
{"type":"status","wiimote":1,"connected":true}
```

Current MQTT translation by the add-on:

```text
topic: wiimote/1/status/connected
payload: true
```

Example heartbeat message from the firmware:

```json
{"type":"heartbeat","device":"esp32","wiimote":1,"connected":true,"battery":87}
```

Current MQTT translation by the add-on:

```text
topic: wiimote/1/status/heartbeat
payload: {"type":"heartbeat","device":"esp32","wiimote":1,"connected":true,"battery":87}
```

## Why This Design

### Why not connect the Wii Remote directly to Home Assistant?

Home Assistant does not provide native Wii Remote support, and Bluetooth HID device handling inside HAOS is a poor fit for a custom integration path like this.

### Why use ESP32?

ESP32 provides:

- inexpensive and widely available hardware
- Bluetooth Classic support
- straightforward firmware development
- a stable USB serial interface to the Home Assistant host

### Why use serial between ESP32 and Home Assistant?

Serial avoids putting WiFi credentials, network stacks, and broker clients into the firmware layer. It also makes the device easy to inspect with a serial monitor during development.

### Why use MQTT as the add-on output?

MQTT is a stable, automation-friendly interface that integrates well with Home Assistant and remains usable outside Home Assistant.

## Failure and Recovery Model

The current architecture tolerates several common failure modes.

### ESP32 Boot or Reset

After startup, the firmware emits:

```json
{"type":"status","device":"esp32","ready":true}
```

The add-on will continue reading when the serial stream resumes.

### Wii Remote Not Yet Paired

The firmware emits prompt and waiting-style status messages such as:

```json
{"type":"status","wiimote":1,"connected":false,"note":"press_1_and_2"}
{"type":"status","wiimote":1,"connected":false,"waiting":true}
```

These are visible in serial logs and forwarded to MQTT events topics.

### Wii Remote Disconnect

The firmware emits:

```json
{"type":"status","wiimote":1,"connected":false}
```

The add-on converts this into MQTT connection state.

### Serial Open Failure

If the add-on cannot open the configured serial device, it logs an error and retries after 5 seconds.

### Active Serial Failure

If the serial device disconnects while the add-on is running, the add-on closes the handle, resets its serial state, and retries after 2 seconds.

### Unexpected Processing Error

If a non-serial exception occurs while processing a line, the add-on logs the exception and continues after 1 second.

## Current Constraints

The current implementation intentionally stays narrow.

Today the full system is best described as:

- one controller-focused bridge
- button-event publishing
- connection-state publishing
- heartbeat forwarding
- battery forwarding and battery topic publishing

Not yet implemented end to end:

- accelerometer MQTT topics
- commands from Home Assistant back to firmware
- LED control
- explicit multi-controller routing

## Planned Evolution

The current boundaries leave room for future expansion.

Likely next protocol and architecture improvements include:

- battery topic publishing in the add-on
- motion and accelerometer events
- bidirectional command topics
- LED state control
- support for more than one connected Wii Remote
