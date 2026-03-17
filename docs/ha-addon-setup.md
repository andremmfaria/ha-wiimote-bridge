# Home Assistant Add-on Setup

This guide covers installation, configuration, validation, and troubleshooting for the WiiMote Bridge add-on in Home Assistant.

The add-on reads JSON events from the ESP32 over USB serial and publishes supported events to MQTT.

When `discover_enabled: true`, Home Assistant MQTT Discovery payloads are published after MQTT connection is confirmed and republished on reconnect.

## Requirements

Before installation, make sure you have:

- Home Assistant OS or Home Assistant Supervised with add-on support
- the ESP32 firmware flashed from `esp32/wiimote-serial-bridge`
- the ESP32 connected to the Home Assistant host over USB
- an MQTT broker, such as the official Mosquitto broker add-on
- a Wii Remote available for pairing

If the firmware is not ready yet, complete `docs/firmware-setup.md` first.

## Install or Verify MQTT

The bridge publishes events through MQTT, so a broker must already be reachable.

Typical Home Assistant path:

```text
Settings -> Add-ons -> Add-on Store
```

Install and start:

```text
Mosquitto broker
```

Then verify the MQTT integration exists under:

```text
Settings -> Devices & Services
```

## Add the Repository

Open the add-on store and add this repository:

```text
https://github.com/andremmfaria/ha-wiimote-bridge
```

Navigation path:

```text
Settings -> Add-ons -> Add-on Store -> menu -> Repositories
```

## Install the Add-on

Find and install:

```text
WiiMote Bridge
```

After install, open the add-on page and move to the configuration tab.

## Configuration

Example configuration:

```yaml
radios:
  - port: /dev/ttyUSB0
    baud: 115200
    controller_id: 1
discover_enabled: true
mqtt_host: core-mosquitto
mqtt_port: 1883
mqtt_username: ""
mqtt_password: ""
mqtt_transport: tcp
mqtt_ssl: false
mqtt_ssl_insecure: false
topic_prefix: wiimote
log_level: info
```

### Option Reference

| Option | Meaning |
| --- | --- |
| `radios` | List of ESP32 radios: each has `port`, `baud`, and `controller_id` |
| `discover_enabled` | Enable/disable Home Assistant MQTT Discovery publishing |
| `mqtt_host` | Hostname or IP of the MQTT broker |
| `mqtt_port` | Broker TCP port |
| `mqtt_username` | Optional MQTT username |
| `mqtt_password` | Optional MQTT password |
| `mqtt_transport` | MQTT transport: `tcp` or `websockets` |
| `mqtt_ssl` | Enable TLS for MQTT connection |
| `mqtt_ssl_insecure` | Disable TLS certificate verification (self-hosted certs) |
| `topic_prefix` | Base topic prefix for all MQTT publications |
| `log_level` | Application log verbosity: `debug`, `info`, `warning`, or `error` |

Due to limitations in the ESP32 Classic HID stack, each ESP32 radio can pair with only one Wii Remote at a time. A single add-on instance manages all configured radios, running one serial reader thread per entry. Add additional entries to `radios` for each extra ESP32 connected to the host.

### Choosing `log_level`

Use:

- `info` for normal operation
- `debug` when validating serial traffic or troubleshooting parsing
- `warning` to reduce noise while keeping warnings and errors
- `error` to show only failures

## Find the Correct Serial Device

In Home Assistant, open:

```text
Settings -> System -> Hardware
```

Look for the ESP32 USB serial entry. Common values are:

- `/dev/ttyUSB0`
- `/dev/ttyUSB1`
- `/dev/ttyACM0`

Use that exact value in `port` under the relevant `radios` entry.

## Start the Add-on

After saving configuration:

1. Open the `Info` tab.
2. Start the add-on.
3. Open the `Logs` tab.

Expected startup output includes a shell summary and application logs such as:

```log
Starting WiiMote Bridge
Application log level: info
MQTT host: core-mosquitto:1883
Topic prefix: wiimote
INFO wiimote_bridge.core.run: Starting WiiMote Bridge application
INFO wiimote_bridge.transport.mqtt_client: Connected to MQTT broker at core-mosquitto:1883
INFO wiimote_bridge.transport.serial_reader: Opening serial port /dev/ttyUSB0 at 115200 baud
INFO wiimote_bridge.radio.1: Serial connection established on /dev/ttyUSB0
```

## Pair the Wii Remote

Press `1 + 2` on the Wii Remote while the firmware and add-on are running.

Once connected, you should see serial lines such as:

```log
INFO wiimote_bridge.radio.1: SERIAL {"type":"status","wiimote":1,"connected":true}
INFO wiimote_bridge.radio.1: SERIAL {"type":"btn","wiimote":1,"btn":"A","down":true}
```

And matching MQTT publication logs such as:

```text
MQTT wiimote/1/button/A -> ON
```

## MQTT Topics Published

### Button Topics

```text
<topic_prefix>/<controller_id>/button/<button_name>
```

Examples:

```text
wiimote/1/button/A
wiimote/1/button/B
wiimote/1/button/PLUS
wiimote/1/button/MINUS
```

Payloads:

- `ON` for press
- `OFF` for release

### Connection State Topic

```text
<topic_prefix>/<controller_id>/status/connected
```

Example:

```text
wiimote/1/status/connected
```

Payloads:

- `true`
- `false`

This topic is retained.

### Heartbeat Topic

```text
<topic_prefix>/<controller_id>/status/heartbeat
```

The payload is the heartbeat JSON forwarded by the bridge, with `wiimote` normalized to the configured `controller_id`.

### Battery Topic

```text
<topic_prefix>/<controller_id>/status/battery
```

Example:

```text
wiimote/1/status/battery
```

Payload example:

```text
87
```

The battery topic is retained so new subscribers can immediately read the latest known value.

### Firmware Event Topics

Every firmware message is also forwarded as event JSON.

Topic patterns:

```text
<topic_prefix>/<controller_id>/events/<type>
<topic_prefix>/device/<device>/events/<type>
```

Examples:

```text
wiimote/1/events/status
wiimote/1/events/battery
wiimote/device/esp32/events/status
```

## What the Add-on Does Not Yet Expose as Dedicated Topics

The firmware emits additional information that does not yet have a dedicated convenience topic, but it is still available through the events MQTT topics:

- firmware `ready` status
- pairing prompt notes
- waiting messages

Those messages also remain visible in add-on serial logs at suitable log levels.

## Example Automation

```yaml
alias: Toggle living room light from Wii Remote A
trigger:
  - platform: mqtt
    topic: wiimote/1/button/A
    payload: "ON"
action:
  - service: light.toggle
    target:
      entity_id: light.living_room
mode: single
```

## Validation Checklist

After installation, verify these in order:

1. The add-on starts and stays running.
2. The logs show a successful MQTT connection.
3. The logs show a successful serial connection.
4. Pressing `1 + 2` on the Wii Remote produces a connected status line.
5. Button presses produce MQTT publications.
6. A Home Assistant automation triggers from one of those topics.

If events are visible but entities are missing, validate retained discovery topics:

```bash
mosquitto_sub -h <broker-host> -p <broker-port> -u <user> -P <pass> -v -R -t 'homeassistant/+/wiimote_+/+/config'
```

Also confirm add-on logs include discovery publication summary lines after MQTT connects.

## Troubleshooting

### No events appear in MQTT

Check:

1. `port` in `radios` is correct.
2. `baud` in `radios` matches firmware.
3. The ESP32 firmware is running and producing valid JSON.
4. The MQTT broker is running and reachable.
5. Your automation is listening to the correct `topic_prefix`.

### `Serial open failed`

Likely causes:

- wrong `port` value in `radios`
- ESP32 disconnected
- USB cable provides power only
- device path changed after reconnect

The add-on retries every 5 seconds.

### `Skipping invalid JSON line`

This usually points to:

- wrong `baud` value in `radios`
- corrupted serial output
- unexpected device on the selected serial port

Set `log_level: debug` and verify the raw serial output with a serial monitor if needed.

### MQTT connection errors

Verify:

1. `mqtt_host` is reachable.
2. `mqtt_port` is correct.
3. Credentials are valid if authentication is enabled.
4. `mqtt_transport` matches broker listener type (`tcp` vs `websockets`).
5. If `mqtt_ssl: true`, use valid certs or set `mqtt_ssl_insecure: true` for self-hosted cert chains.

During temporary broker outages or reconnects, the bridge skips MQTT publishes and logs a warning at most once every 15 seconds until connectivity returns.

After broker recovery, discovery is republished automatically on reconnect.

## Entities vs Raw MQTT Automations

The add-on supports both patterns at the same time:

- Home Assistant entities through MQTT Discovery for UI-friendly diagnostics and entity-based automations
- direct MQTT topics for low-level trigger/payload handling

Use raw topics when you need direct control over payload semantics or event stream handling.

## Stopping the Add-on

Stopping the add-on disconnects the MQTT client and stops topic publication. The ESP32 firmware continues running until power or USB is removed.

## Next Steps

Once the add-on is stable, you can build higher-level automations around:

- lights and scenes
- media controls
- connection-state notifications
- heartbeat monitoring

For release hardening, run the full checklist in `docs/release-checklist.md`.
