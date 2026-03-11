# Home Assistant Add-on: WiiMote Bridge

Bridge a Nintendo Wii Remote to Home Assistant using an ESP32 over USB serial.

## Requirements

- Home Assistant OS or Home Assistant Supervised with add-on support
- An ESP32 flashed with the firmware from this repository
- A USB connection between the ESP32 and the Home Assistant host
- An MQTT broker, such as the Mosquitto broker add-on

## Configuration

Example add-on configuration:

```yaml
serial_port: /dev/ttyUSB0
serial_baud: 115200
mqtt_host: core-mosquitto
mqtt_port: 1883
mqtt_username: ""
mqtt_password: ""
topic_prefix: wiimote
```

## Usage

1. Flash the ESP32 firmware from this repository.
2. Connect the ESP32 to the Home Assistant host over USB.
3. Install and start the Mosquitto broker add-on.
4. Install this add-on and set the serial device shown in Home Assistant hardware settings.
5. Start the add-on and press `1 + 2` on the Wii Remote to pair it.

Button events are published as MQTT topics such as:

```text
wiimote/1/button/A
wiimote/1/button/B
wiimote/1/button/PLUS
```

Payloads are `ON` and `OFF`.

## Support

Repository documentation:

- `docs/firmware-setup.md`
- `docs/ha-addon-setup.md`
- `docs/protocol.md`
