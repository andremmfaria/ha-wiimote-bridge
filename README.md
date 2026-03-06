# Home Assistant WiiMote Bridge Add-on

Reads Wii Remote button events from an ESP32 over USB serial and publishes them to MQTT.

## Architecture

Wii Remote  
→ Bluetooth  
→ ESP32  
→ USB serial  
→ Home Assistant add-on  
→ MQTT

## Requirements

- Home Assistant OS
- Mosquitto broker add-on or another MQTT broker
- ESP32 running the WiiMote serial bridge firmware
- USB connection from ESP32 to the HAOS host

## Installation

Add this repository URL to Home Assistant:

`https://github.com/andremmfaria/ha-wiimote-bridge`

Then install the **WiiMote Bridge** add-on.

## Configuration

Example:

```yaml
serial_port: /dev/ttyUSB0
serial_baud: 115200
mqtt_host: core-mosquitto
mqtt_port: 1883
mqtt_username: ""
mqtt_password: ""
topic_prefix: wiimote
```
