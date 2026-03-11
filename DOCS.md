# WiiMote Bridge

This add-on connects a Nintendo Wii Remote to Home Assistant using an ESP32.

The ESP32 handles Bluetooth communication with the controller and sends events to Home Assistant over USB serial.

The add-on reads these events and publishes them to MQTT.

## Architecture

Wii Remote  
↓ Bluetooth  
ESP32 firmware  
↓ USB Serial  
WiiMote Bridge Add-on  
↓ MQTT  
Home Assistant

## Requirements

- ESP32 running the firmware from this repository
- USB connection between ESP32 and Home Assistant host
- Mosquitto MQTT broker add-on

## Configuration

Example configuration:

```yaml
serial_port: /dev/ttyUSB0
serial_baud: 115200
mqtt_host: core-mosquitto
mqtt_port: 1883
topic_prefix: wiimote
```

## Pairing

Press 1 + 2 on the Wii Remote to pair.

Button presses will appear on MQTT topics like:

```
wiimote/1/button/A
```

Payloads:

```
ON
OFF
```
