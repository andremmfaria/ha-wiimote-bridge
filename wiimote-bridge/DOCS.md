# Home Assistant Add-on: WiiMote Bridge

Use this add-on to bridge a Nintendo Wii Remote into Home Assistant through an ESP32 connected by USB serial.

The ESP32 handles Bluetooth pairing and reads button events from the controller. The add-on reads newline-delimited JSON messages from the ESP32 over a serial device, translates them into MQTT topics, and exposes them for Home Assistant automations.

## What This Add-on Does

The running data flow is:

```text
Wii Remote
  -> Bluetooth Classic
ESP32 firmware
  -> USB serial JSON messages
WiiMote Bridge add-on
  -> MQTT topics
Home Assistant automations, dashboards, or other MQTT consumers
```

At runtime, the add-on performs these steps:

1. Reads the add-on options from Home Assistant.
2. Exports them as environment variables into the container.
3. Configures application logging.
4. Connects to the configured MQTT broker.
5. Opens the configured serial device.
6. Reads line-delimited serial messages from the ESP32.
7. Parses valid JSON messages.
8. Publishes button, connection, and heartbeat messages to MQTT.

The add-on automatically retries when the serial connection is unavailable or temporarily disconnected.

## Requirements

Before installing this add-on, make sure the following pieces are ready:

- Home Assistant OS or Home Assistant Supervised with add-on support.
- An ESP32 board flashed with the firmware included in this repository.
- A USB connection from the ESP32 to the Home Assistant host.
- An MQTT broker reachable from Home Assistant, such as the Mosquitto broker add-on.
- A standard Nintendo Wii Remote.

Recommended prerequisites:

- Confirm the MQTT integration is already working in Home Assistant.
- Confirm the ESP32 appears under Home Assistant hardware information as a serial device such as `/dev/ttyUSB0` or `/dev/ttyACM0`.
- Confirm the firmware baud rate matches the add-on baud setting.

## Installation

1. Add this repository to the Home Assistant add-on store.
2. Install the `WiiMote Bridge` add-on.
3. Install and start an MQTT broker if one is not already available.
4. Connect the ESP32 over USB to the Home Assistant host.
5. Open the add-on configuration tab and set the correct serial and MQTT values.
6. Start the add-on.
7. Open the logs and confirm the application started correctly.
8. Press `1 + 2` on the Wii Remote to pair it through the ESP32 firmware.

For a more guided setup flow, see the repository documentation:

- `docs/firmware-setup.md`
- `docs/ha-addon-setup.md`
- `docs/protocol.md`
- `docs/architecture.md`

## Configuration

Example add-on configuration:

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
topic_prefix: wiimote
log_level: info
```

### Option Reference

#### `radios`

A list of ESP32 radios connected to this host. Each entry defines one serial device and its assigned controller identifier.

Each entry contains:

`port`: the serial device path exposed by the Home Assistant host, e.g. `/dev/ttyUSB0`.
`baud`: the serial baud rate used by the ESP32 firmware. Must match the firmware configuration.
`controller_id`: bridge-side integer identifier used in all MQTT topic paths for this radio.

Multiple radios example:

```yaml
radios:
  - port: /dev/ttyUSB0
    baud: 115200
    controller_id: 1
  - port: /dev/ttyUSB1
    baud: 115200
    controller_id: 2
```

Due to limitations in the ESP32 Classic HID stack, each ESP32 radio can pair with only one Wii Remote at a time. One add-on instance manages all radios, opening a dedicated serial reader thread per entry.

#### `discover_enabled`

Controls whether the add-on publishes Home Assistant MQTT Discovery config topics after a confirmed MQTT connection.

Default:

```text
true
```

When enabled, discovery payloads are also republished after MQTT reconnects. Set this to `false` if you want to manage entities manually and disable auto-discovery.

#### `mqtt_host`

Hostname of the MQTT broker.

Common values:

- `core-mosquitto` for the official Mosquitto add-on.
- A LAN hostname or IP address for an external broker.

#### `mqtt_port`

TCP port used to connect to the MQTT broker.

Default:

```text
1883
```

#### `mqtt_username`

Optional MQTT username.

Leave this empty if your broker accepts anonymous clients on the configured network.

#### `mqtt_password`

Optional MQTT password.

Only used when `mqtt_username` is non-empty.

#### `topic_prefix`

Base prefix for all published MQTT topics.

Default:

```text
wiimote
```

If you change this option, every topic published by the add-on will move under the new prefix.

#### `log_level`

Controls how much application output is written to the add-on logs.

Allowed values:

- `debug`
- `info`
- `warning`
- `error`

Recommended values:

- Use `info` for normal operation.
- Use `debug` while validating serial traffic, JSON parsing, or MQTT publication.
- Use `warning` or `error` only if you want reduced log volume.

## How Device Access Works

This add-on enables Home Assistant serial device mapping through:

```yaml
uart: true
```

That allows the container to access host serial devices without manually defining device mounts.

To find the correct serial device in Home Assistant:

1. Open `Settings -> System -> Hardware`.
2. Find the ESP32 USB serial entry.
3. Copy the device path.
4. Paste that value into `port` under the relevant `radios` entry.

## Application Startup Sequence

When the add-on starts, `run.sh` reads your Home Assistant options and prints a short startup summary, including:

- configured radio ports and baud rates
- MQTT host and port
- MQTT topic prefix
- configured log level

The Python application then logs its own runtime initialization. Under normal conditions, startup looks similar to this:

```log
Starting WiiMote Bridge
Application log level: info
MQTT host: core-mosquitto:1883
Topic prefix: wiimote
INFO wiimote_bridge.core.run: Starting WiiMote Bridge application
INFO wiimote_bridge.core.run: Log level: INFO
INFO wiimote_bridge.core.run: Radio: /dev/ttyUSB0 @ 115200 baud, controller ID 1
INFO wiimote_bridge.transport.mqtt_client: Connected to MQTT broker at core-mosquitto:1883
INFO wiimote_bridge.transport.serial_reader: Opening serial port /dev/ttyUSB0 at 115200 baud
INFO wiimote_bridge.radio.1: Serial connection established on /dev/ttyUSB0
```

## Runtime Behavior

The application reads one serial line at a time.

For each line:

1. The line is decoded from bytes to text.
2. Empty lines are ignored.
3. The raw line is logged as `SERIAL ...`.
4. Non-JSON lines are ignored.
5. Invalid JSON lines generate a warning.
6. Valid JSON objects are dispatched according to their `type`.

Supported incoming message types:

- `btn`
- `status`
- `heartbeat`
- `battery`

## MQTT Topics Published by the Add-on

## Home Assistant MQTT Discovery

After MQTT connection is confirmed, the add-on publishes retained MQTT Discovery config topics so Home Assistant can auto-create entities for each configured `controller_id`.

The add-on republishes discovery topics after MQTT reconnects. Since config topics are retained and unique IDs are stable, this is idempotent and updates the same Home Assistant entities instead of creating duplicates.

Discovery prefix:

```text
homeassistant
```

Entity types created per controller:

- Connectivity binary sensor (`.../status/connected`)
- Battery sensor (`.../status/battery`)
- Button binary sensors for `A`, `B`, `UP`, `DOWN`, `LEFT`, `RIGHT`, `PLUS`, `MINUS`, `HOME`, `ONE`, `TWO`

Button entities are intentionally modeled as binary sensors because the bridge publishes button edge transitions (`ON` for press, `OFF` for release), which align with binary sensor semantics and Home Assistant automations.

### Button Events

Button press and release events are published to:

```text
<topic_prefix>/<controller_id>/button/<button_name>
```

Examples:

```text
wiimote/1/button/A
wiimote/1/button/B
wiimote/1/button/PLUS
wiimote/1/button/HOME
```

Payloads:

- `ON` when the button is pressed
- `OFF` when the button is released

These button messages are published with `retain=false`.

### Connection Status

Connection state events are published to:

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

This topic is published with `retain=true`, which allows subscribers to immediately see the latest known connection state.

### Battery Status

Battery updates are published to:

```text
<topic_prefix>/<controller_id>/status/battery
```

Example:

```text
wiimote/1/status/battery
```

Payload:

```text
87
```

With the current ESP32Wiimote library, battery values are forwarded as percentage (`0-100`).

This topic is published with `retain=true` so the latest known battery value remains available to subscribers.

### Heartbeat Messages

Heartbeat messages are published to:

```text
<topic_prefix>/<controller_id>/status/heartbeat
```

Example payload:

```json
{"type":"heartbeat","device":"esp32","wiimote":1,"connected":true}
```

This topic is published with `retain=false`.

If the payload contains a `wiimote` field, the bridge rewrites it to the configured `controller_id` before publishing.

### Event Topics

Every incoming firmware message is also forwarded as event JSON so nothing is lost even when the bridge does not expose a dedicated convenience topic shape.

Topics:

```text
<topic_prefix>/<controller_id>/events/<type>
<topic_prefix>/device/<device>/events/<type>
```

Examples:

```text
wiimote/1/events/status
wiimote/1/events/battery
wiimote/1/events/heartbeat
wiimote/device/esp32/events/status
```

These event topics carry the firmware JSON payload, with `wiimote` normalized to the configured `controller_id` when present.

## Serial Protocol Examples

Typical serial messages from the ESP32 look like this:

```json
{"type":"status","device":"esp32","ready":true}
{"type":"status","wiimote":1,"connected":true}
{"type":"btn","wiimote":1,"btn":"A","down":true}
{"type":"btn","wiimote":1,"btn":"A","down":false}
{"type":"heartbeat","device":"esp32","wiimote":1,"connected":true}
```

The add-on currently maps them like this:

| Serial message type | MQTT output |
| --- | --- |
| `btn` | Publishes `ON` or `OFF` to a button topic |
| `status` with `connected` | Publishes `true` or `false` to the connection topic |
| `heartbeat` | Publishes the full JSON object to the heartbeat topic |
| `battery` | Publishes battery level to the battery topic |
| any message | Publishes the original JSON object to an events topic |

Firmware `ready`, `waiting`, and `note` messages are available through the events topics.

## Example Home Assistant Automations

### Toggle a Light with the A Button

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

### Trigger a Scene with the PLUS Button

```yaml
alias: Activate movie scene from Wii Remote PLUS
trigger:
  - platform: mqtt
    topic: wiimote/1/button/PLUS
    payload: "ON"
action:
  - service: scene.turn_on
    target:
      entity_id: scene.movie_time
mode: single
```

### React to Controller Connection State

```yaml
alias: Notify when Wii Remote connects
trigger:
  - platform: mqtt
    topic: wiimote/1/status/connected
    payload: "true"
action:
  - service: persistent_notification.create
    data:
      title: Wii Remote connected
      message: The Wii Remote is connected and ready.
mode: single
```

## Logging

The add-on exposes both shell-level startup logs and Python application logs in the Home Assistant log viewer.

### Log Levels

The Python application accepts four log levels:

- `debug`
- `info`
- `warning`
- `error`

Behavior by level:

- `debug` includes extra diagnostic lines such as non-JSON line skipping and configuration hints.
- `info` includes normal startup, serial, and MQTT activity.
- `warning` suppresses normal operational chatter and keeps warnings and errors.
- `error` only keeps error-level failures.

### Useful Log Lines

Normal startup:

```log
INFO wiimote_bridge.core.run: Starting WiiMote Bridge application
INFO wiimote_bridge.transport.mqtt_client: Connected to MQTT broker at core-mosquitto:1883
INFO wiimote_bridge.transport.serial_reader: Opening serial port /dev/ttyUSB0 at 115200 baud
INFO wiimote_bridge.radio.1: Serial connection established on /dev/ttyUSB0
```

Normal event flow:

```log
INFO wiimote_bridge.radio.1: SERIAL {"type":"btn","wiimote":1,"btn":"A","down":true}
INFO wiimote_bridge.transport.mqtt_client: MQTT wiimote/1/button/A -> ON
```

Serial problems:

```log
ERROR wiimote_bridge.radio.1: Serial open failed on /dev/ttyUSB0: ...
ERROR wiimote_bridge.radio.1: Serial error on /dev/ttyUSB0: ...
```

Malformed input:

```log
WARNING wiimote_bridge.radio.1: Skipping invalid JSON line
```

Shutdown:

```log
INFO wiimote_bridge.core.run: Received signal 15, shutting down
INFO wiimote_bridge.core.run: MQTT client disconnected
```

## Failure Handling and Recovery

The add-on contains basic recovery logic:

- If the serial device cannot be opened, the app logs the error and retries after 5 seconds.
- If an active serial session raises `serial.SerialException`, the device is closed, the connection is reset, and the app retries after 2 seconds.
- If any other unexpected exception occurs while processing a message, the stack trace is logged and the loop continues after 1 second.
- If MQTT is disconnected when publishing, the message is skipped and a warning is logged at most once every 15 seconds.
- On container stop, the app closes the serial device, stops the MQTT client loop, and disconnects from the broker.

This means temporary serial disconnects or ESP32 resets usually do not require a full add-on reinstall.

## Troubleshooting

### The Add-on Starts but No Button Events Appear

Check the following:

1. The ESP32 is powered and connected by USB.
2. The `port` in `radios` matches the actual host device.
3. The firmware baud rate matches `baud` in `radios`.
4. The Wii Remote is paired with the ESP32.
5. The MQTT broker is running and reachable.
6. `topic_prefix` matches the topic you are subscribing to.

### The Logs Show `Serial open failed`

Common causes:

- Wrong `port` value in `radios`.
- ESP32 not detected by the host.
- USB cable only provides power and not data.
- The device changed from `/dev/ttyUSB0` to another path after reconnecting.

### The Logs Show `Skipping invalid JSON line`

This usually means one of the following:

- Baud rate mismatch between `baud` in `radios` and the firmware.
- Firmware output is corrupted.
- Another device is using the same serial adapter unexpectedly.

Try:

1. Reconfirm the baud rate.
2. Set `log_level: debug`.
3. Reboot the ESP32.
4. Check the firmware setup documentation.

### The Logs Show MQTT Connection Problems

Verify:

1. `mqtt_host` resolves from inside Home Assistant.
2. `mqtt_port` is correct.
3. `mqtt_username` and `mqtt_password` are valid if authentication is required.
4. The broker accepts connections from the add-on network.

During temporary MQTT outages or reconnects, warning lines like the following are expected:

```log
WARNING wiimote_bridge.transport.mqtt_client: Skipping MQTT publish while client is disconnected: ...
```

This warning is rate-limited to once every 15 seconds while disconnected.

Discovery readiness and publication lines now include:

```log
INFO wiimote_bridge.transport.mqtt_client: Connected to MQTT broker at core-mosquitto:1883
INFO wiimote_bridge.transport.mqtt_client: Publishing MQTT discovery for 1 controller(s); expecting 13 entity configs
INFO wiimote_bridge.transport.mqtt_client: MQTT discovery publish completed successfully: 13 entities announced
```

If some discovery entities fail to publish:

```log
WARNING wiimote_bridge.transport.mqtt_client: MQTT discovery publish completed with failures: 1/13 entities failed
```

### The Add-on Installs but Home Assistant Cannot Pull the Image

This is a release and registry issue, not an application issue.

Check that:

1. The add-on release workflow ran for a `v<version>` tag.
2. The version in `config.yaml` matches the pushed git tag.
3. The GHCR package exists and is public.

## Operational Notes

- The application currently provides dedicated MQTT topics for button events, connection state, battery level, and heartbeat messages.
- Every firmware message is also forwarded to an events JSON MQTT topic.
- Home Assistant entities (via discovery) and raw MQTT-topic automations can be used side by side.
- Discovery payloads are republished on MQTT reconnect, so Home Assistant can recover without relying on startup timing.
- Motion, rumble, LED control, and inbound command topics are not yet implemented in the add-on.
- Each ESP32 radio supports one paired Wii Remote with ESP32Wiimote.
- Multiple Wii Remotes on one host require multiple ESP32 radios and multiple add-on instances with distinct `controller_id` values.

## Retained Discovery Validation

Use this procedure to verify discovery topics are present and durable.

1. Start the add-on and confirm discovery publication logs appear after MQTT connects.
2. Query retained discovery config topics on the broker:

```bash
mosquitto_sub -h <broker-host> -p <broker-port> -u <user> -P <pass> -v -R -t 'homeassistant/+/wiimote_+/+/config'
```

3. Confirm each configured controller has:

- one connectivity binary sensor discovery topic
- one battery sensor discovery topic
- one discovery topic per supported button

4. Confirm payload state topics match runtime topics:

- `<topic_prefix>/<controller_id>/status/connected`
- `<topic_prefix>/<controller_id>/status/battery`
- `<topic_prefix>/<controller_id>/button/<BUTTON>`

5. Restart Home Assistant only and confirm entities are rebuilt from retained discovery topics without forcing add-on restart.
6. Restart the MQTT broker and confirm discovery gets republished after reconnect.

## Recommended Validation Checklist

After installation, verify these items in order:

1. The add-on starts without exiting.
2. The logs show a successful MQTT connection.
3. The logs show a successful serial connection.
4. Pairing the controller produces `SERIAL` log lines.
5. MQTT button topics receive `ON` and `OFF` payloads.
6. A Home Assistant automation can trigger from one of those topics.

## Related Documentation

- `docs/firmware-setup.md`
- `docs/ha-addon-setup.md`
- `docs/protocol.md`
- `docs/architecture.md`
- `README.md`
