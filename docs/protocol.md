# Serial Protocol

This document defines the JSON protocol spoken by the ESP32 firmware over USB serial.

The Home Assistant add-on consumes this protocol line by line and forwards every message to MQTT.

## Transport Rules

The protocol is emitted as line-delimited JSON.

Rules:

- each line is one JSON object
- objects are newline-terminated
- ordering is preserved
- there is no framing beyond newlines
- the serial speed is `115200`

Example stream:

```text
{"type":"status","device":"esp32","ready":true}
{"type":"status","wiimote":1,"connected":false,"note":"press_1_and_2"}
{"type":"status","wiimote":1,"connected":true}
{"type":"btn","wiimote":1,"btn":"A","down":true}
{"type":"btn","wiimote":1,"btn":"A","down":false}
{"type":"heartbeat","device":"esp32","wiimote":1,"connected":true,"battery":87}
{"type":"battery","wiimote":1,"level":87}
```

## Message Types

### `status`

Status messages are used for firmware lifecycle state, connection state, and operator hints.

#### Firmware Ready

```json
{"type":"status","device":"esp32","ready":true}
```

Fields:

| Field | Meaning |
| --- | --- |
| `type` | Always `status` |
| `device` | Device identifier, currently `esp32` |
| `ready` | Firmware boot completed |

#### Pairing Prompt

```json
{"type":"status","wiimote":1,"connected":false,"note":"press_1_and_2"}
```

Fields:

| Field | Meaning |
| --- | --- |
| `type` | Always `status` |
| `wiimote` | Controller identifier |
| `connected` | Current connection state |
| `note` | Human-oriented pairing hint |

#### Waiting State

```json
{"type":"status","wiimote":1,"connected":false,"waiting":true}
```

This is emitted periodically while the controller is not connected.

#### Connection State

```json
{"type":"status","wiimote":1,"connected":true}
```

This is emitted when the controller connects or disconnects.

Fields:

| Field | Meaning |
| --- | --- |
| `type` | Always `status` |
| `wiimote` | Controller identifier |
| `connected` | `true` or `false` |

### `btn`

Button messages represent edge transitions, not a continuously repeated state stream.

Press example:

```json
{"type":"btn","wiimote":1,"btn":"A","down":true}
```

Release example:

```json
{"type":"btn","wiimote":1,"btn":"A","down":false}
```

Fields:

| Field | Meaning |
| --- | --- |
| `type` | Always `btn` |
| `wiimote` | Controller identifier |
| `btn` | Button name |
| `down` | `true` for press, `false` for release |

Supported button names:

```text
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

### `heartbeat`

Heartbeat messages confirm the firmware is alive and include current connection state.

Example while connected:

```json
{"type":"heartbeat","device":"esp32","wiimote":1,"connected":true,"battery":87}
```

Example while disconnected:

```json
{"type":"heartbeat","device":"esp32","wiimote":1,"connected":false}
```

Fields:

| Field | Meaning |
| --- | --- |
| `type` | Always `heartbeat` |
| `device` | Device identifier |
| `wiimote` | Controller identifier |
| `connected` | Current connection state |
| `battery` | Present when a connected controller battery value is known |

Current interval:

```text
10 seconds
```

### `battery`

Battery messages are emitted when the battery level changes.

Example:

```json
{"type":"battery","wiimote":1,"level":87}
```

Fields:

| Field | Meaning |
| --- | --- |
| `type` | Always `battery` |
| `wiimote` | Controller identifier |
| `level` | Battery percentage (`0-100`) |

## Add-on Mapping

The current add-on publishes both convenience topics and passthrough events topics.

A single add-on instance manages all configured ESP32 radios, operating one serial reader thread per radio. Each radio entry has its own `controller_id`, which the add-on uses in all MQTT topic paths and to rewrite any incoming `wiimote` field before publishing.

Current mapping:

| Serial message | MQTT result |
| --- | --- |
| any message with `wiimote` | Published as event JSON to `<prefix>/<id>/events/<type>` |
| any message with `device` but no `wiimote` | Published as event JSON to `<prefix>/device/<device>/events/<type>` |
| `btn` | Published to `<prefix>/<id>/button/<button>` with `ON` or `OFF` |
| `status` with `connected` | Published to `<prefix>/<id>/status/connected` with `true` or `false` |
| `heartbeat` | Published to `<prefix>/<id>/status/heartbeat` as JSON |
| `battery` | Published to `<prefix>/<id>/status/battery` with the numeric level |

This means every valid firmware message now reaches MQTT even if there is no dedicated high-level topic for it yet.

## Ordering and State Semantics

The firmware emits messages sequentially. Button events are emitted on transitions only.

Additionally, the firmware captures the first observed button state after a connection and uses it as a baseline. This avoids emitting false transition events immediately after connection.

## Design Goals

The protocol is designed to be:

- human-readable
- easy to inspect with a serial monitor
- simple to parse incrementally
- independent of Home Assistant
- extensible for new event types

Any system capable of reading line-delimited JSON over serial can consume it.

## Future Extensions

Likely future additions include:

- accelerometer events
- command messages from the bridge to firmware
- rumble control
- LED control
