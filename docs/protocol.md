# Serial Protocol

This document defines the JSON protocol used between the ESP32 firmware and the Home Assistant bridge add-on.

The ESP32 emits newline-delimited JSON messages over USB serial.

Each message is a single JSON object.

Example stream:

```
{"type":"status","device":"esp32","ready":true}
{"type":"status","wiimote":1,"connected":true}
{"type":"btn","wiimote":1,"btn":"A","down":true}
{"type":"btn","wiimote":1,"btn":"A","down":false}
{"type":"heartbeat","device":"esp32","wiimote":1,"connected":true}
```

Messages are emitted as **line-delimited JSON (LDJSON)**.

This makes parsing simple and allows the bridge to process events incrementally.

---

# Message Types

## Status

Status messages describe device state.

Example:

```
{"type":"status","device":"esp32","ready":true}
```

Fields:

| Field | Description |
| ------ | ------------- |
| type | `status` |
| device | identifier of the emitting device |
| ready | firmware boot complete |

---

## Wiimote Connection Status

Example:

```
{"type":"status","wiimote":1,"connected":true}
```

Fields:

| Field | Description |
| ------ | ------------- |
| type | `status` |
| wiimote | controller identifier |
| connected | connection state |

Connection status is emitted when the Wiimote connects.

---

## Button Event

Example:

```
{"type":"btn","wiimote":1,"btn":"A","down":true}
```

Fields:

| Field | Description |
| ------ | ------------- |
| type | `btn` |
| wiimote | controller identifier |
| btn | button name |
| down | `true` if pressed |

Release event:

```
{"type":"btn","wiimote":1,"btn":"A","down":false}
```

---

# Button Names

Supported button identifiers:

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

These names are chosen to match the labels on the Wii Remote.

---

# Heartbeat

Example:

```
{"type":"heartbeat","device":"esp32","wiimote":1,"connected":true}
```

Heartbeat messages are emitted periodically by the firmware.

Purpose:

- allow the bridge to detect stale serial connections
- confirm firmware is still running
- confirm Wiimote connection state

Current interval:

```
10 seconds
```

---

# Message Ordering

The firmware guarantees that:

- messages are emitted sequentially
- each message is a complete JSON object
- messages are separated by newline characters

Example raw serial stream:

```
{"type":"btn","wiimote":1,"btn":"A","down":true}
{"type":"btn","wiimote":1,"btn":"A","down":false}
```

---

# Future Extensions

The protocol is intentionally extensible.

Possible future message types:

## Accelerometer

```
{"type":"accel","wiimote":1,"x":0.12,"y":-0.05,"z":0.98}
```

## Battery Level

```
{"type":"battery","wiimote":1,"level":87}
```

## Rumble Control

Bridge → firmware:

```
{"type":"cmd","wiimote":1,"rumble":true}
```

## LED Control

```
{"type":"cmd","wiimote":1,"led":2}
```

---

# Design Goals

The protocol was designed to be:

- human readable
- easy to parse
- extensible
- independent of Home Assistant

Any system capable of reading JSON over serial can consume the events.
