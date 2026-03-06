# System Architecture

This project converts a Nintendo Wii Remote into a Home Assistant controller using an ESP32 and a USB serial bridge.

The system consists of three main components.

---

# Overview

```
Wii Remote
↓ Bluetooth (HID)
ESP32 Firmware
↓ USB Serial
Home Assistant Add-on
↓ MQTT
Home Assistant Automations
```

---

# Component Responsibilities

## Wii Remote

The Wii Remote acts as the input device.

Capabilities:

- digital buttons
- accelerometer
- IR tracking
- rumble motor
- LEDs

Currently used features:

```
button input
```

Future firmware versions may add motion support.

---

# ESP32 Firmware

The ESP32 acts as a Bluetooth host and translates Wii Remote events into JSON messages.

Responsibilities:

- connect to the Wii Remote
- read button states
- detect button state changes
- emit JSON messages over serial
- provide heartbeat messages

The ESP32 does **not** connect to WiFi.

Communication with Home Assistant is done entirely over USB serial.

Advantages:

- simple
- reliable
- avoids WiFi configuration
- avoids Bluetooth complexity inside Home Assistant

---

# USB Serial Bridge

The ESP32 connects to the Home Assistant host via USB.

This provides:

```
ESP32 → /dev/ttyUSB*
```

The Home Assistant add-on reads the serial stream and parses JSON messages.

---

# Home Assistant Add-on

The add-on performs protocol translation.

Responsibilities:

- read serial messages
- parse JSON events
- publish MQTT topics

Example translation:

Serial input:

```
{"type":"btn","wiimote":1,"btn":"A","down":true}
```

MQTT output:

```
topic: wiimote/1/button/A
payload: ON
```

---

# MQTT

MQTT provides the messaging layer between the bridge and Home Assistant.

Example topics:

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

This makes the project compatible with many systems:

- Home Assistant
- Node-RED
- openHAB
- custom scripts

---

# Home Assistant

Home Assistant uses MQTT triggers to create automations.

Example automation:

```
trigger:

* platform: mqtt
  topic: wiimote/1/button/A
  payload: "ON"
```

Actions can control:

- lights
- scenes
- media players
- scripts

---

# Why This Architecture

The design intentionally avoids several common pitfalls.

## Why not connect the Wiimote directly to Home Assistant?

Home Assistant does not support Wii Remote HID input devices.

Bluetooth stacks for HID devices inside HAOS are also difficult to manage.

---

## Why use ESP32?

ESP32 provides:

- inexpensive hardware
- reliable Bluetooth Classic support
- easy firmware development
- simple USB serial interface

---

## Why use MQTT?

MQTT allows the system to be reused outside Home Assistant.

Other consumers can subscribe to the same topics.

---

# Failure Handling

The architecture is resilient to failures.

## ESP32 reset

The firmware emits:

```
{"type":"status","device":"esp32","ready":true}
```

## Wiimote disconnect

Connection status changes:

```
{"type":"status","wiimote":1,"connected":false}
```

## Serial interruption

The add-on automatically reconnects to the serial device.

---

# Future Architecture Improvements

Planned improvements include:

## Motion Control

Expose accelerometer data for gesture-based automations.

Example:

```
shake → toggle lights
tilt → dim lights
```

---

## Rumble Feedback

Allow Home Assistant to send commands back to the ESP32 to activate the Wii Remote rumble motor.

---

## LED State

Use the Wii Remote LEDs to indicate Home Assistant states.

Examples:

- armed alarm
- active scene
- notification indicator

---

## Multiple Controllers

Support for multiple Wii Remotes.

Example MQTT topics:

```
wiimote/1/button/A
wiimote/2/button/A
```
