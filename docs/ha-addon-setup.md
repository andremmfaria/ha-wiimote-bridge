# Home Assistant Add-on Setup

This guide explains how to install and configure the WiiMote Bridge add-on in Home Assistant.

The add-on reads JSON events from the ESP32 over USB serial and publishes them to MQTT so Home Assistant automations can use them.

---

# Requirements

Before installing the add-on, make sure you have:

- Home Assistant OS
- an ESP32 running the firmware from `esp32/wiimote_serial_bridge`
- the ESP32 connected to the Home Assistant host via USB
- the Mosquitto MQTT broker add-on installed

If you have not flashed the firmware yet, follow:

```
docs/firmware-setup.md
```

---

# Install the MQTT Broker

The bridge publishes events to MQTT, so a broker must be running.

Install the official **Mosquitto broker** add-on.

In Home Assistant:

```
Settings → Add-ons → Add-on Store
```

Install:

```
Mosquitto broker
```

Start the add-on.

Once started, the MQTT integration should automatically appear in Home Assistant.

If not, add it manually:

```
Settings → Devices & Services → Add Integration → MQTT
```

---

# Add the Repository

The WiiMote Bridge add-on is installed from a custom repository.

Open the add-on store.

```
Settings → Add-ons → Add-on Store
```

Click the **three dots menu** in the top right.

Select:

```
Repositories
```

Add your repository URL:

```
[https://github.com/andremmfaria/ha-wiimote-bridge](https://github.com/andremmfaria/ha-wiimote-bridge)
```

Click **Add**.

The new add-on should now appear in the store.

---

# Install the Add-on

Find the add-on:

```
WiiMote Bridge
```

Click **Install**.

Once installation completes, open the add-on page.

---

# Configure the Add-on

Open the **Configuration** tab.

Example configuration:

```yaml
serial_port: /dev/ttyUSB0
serial_baud: 115200
mqtt_host: core-mosquitto
mqtt_port: 1883
mqtt_username: ""
mqtt_password: ""
topic_prefix: wiimote
```

Explanation:

| Option        | Description                        |
| ------------- | ---------------------------------- |
| serial_port   | serial device used by the ESP32    |
| serial_baud   | serial speed (must match firmware) |
| mqtt_host     | hostname of the MQTT broker        |
| mqtt_port     | MQTT port                          |
| mqtt_username | optional MQTT username             |
| mqtt_password | optional MQTT password             |
| topic_prefix  | base topic for published messages  |

---

# Find the Serial Device

If you are unsure which serial device your ESP32 uses, go to:

```
Settings → System → Hardware
```

Look for a USB serial device.

Examples:

```
/dev/ttyUSB0
/dev/ttyUSB1
/dev/ttyACM0
```

Update the add-on configuration accordingly.

---

# Start the Add-on

After saving the configuration:

1. Go to the **Info** tab
2. Click **Start**

Then open the **Logs** tab.

You should see messages similar to:

```
Starting WiiMote Bridge
Serial port: /dev/ttyUSB0
Connected to MQTT broker
Opening serial device
```

Once the ESP32 connects you will see lines like:

```
SERIAL {"type":"status","wiimote":1,"connected":true}
SERIAL {"type":"btn","wiimote":1,"btn":"A","down":true}
MQTT wiimote/1/button/A -> ON
```

---

# Pair the Wii Remote

Press:

```
1 + 2
```

on the Wii Remote.

The ESP32 firmware will connect and begin sending events.

---

# MQTT Topics

Button events are published to MQTT.

Example topics:

```
wiimote/1/button/A
wiimote/1/button/B
wiimote/1/button/PLUS
wiimote/1/button/MINUS
```

Payload values:

```
ON
OFF
```

Example:

```
topic: wiimote/1/button/A
payload: ON
```

---

# Create a Home Assistant Automation

You can now use MQTT triggers.

Example automation:

```yaml
alias: Wii Remote A Button
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

---

# Debugging

If button presses do not appear:

1. Check the add-on logs
2. Confirm the correct serial port
3. Confirm the ESP32 firmware is running
4. Confirm the MQTT broker is running

You can also monitor MQTT traffic using tools such as:

```
MQTT Explorer
```

Subscribe to:

```
wiimote/#
```

---

# Stopping the Add-on

To stop the bridge:

```
Add-on → Info → Stop
```

The ESP32 firmware will continue running but no MQTT events will be published until the add-on is restarted.

---

# Next Steps

Once the bridge is working you can:

* create Home Assistant automations
* control scenes and media players
* experiment with gesture-based control (future firmware updates)

Future features planned for the project include:

* accelerometer events
* rumble control
* LED status feedback
* support for multiple Wii Remotes
