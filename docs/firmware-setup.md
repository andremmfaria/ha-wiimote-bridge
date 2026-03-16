# Firmware Setup

This guide covers building, flashing, and validating the ESP32 firmware used by the WiiMote Bridge project.

The firmware does three main jobs:

1. Connect to a Wii Remote over Bluetooth Classic.
2. Convert controller state changes into JSON messages.
3. Emit those messages over USB serial for the Home Assistant add-on.

## What the Firmware Emits

The current firmware sends line-delimited JSON over the serial port. Depending on state, you can see messages such as:

```json
{"type":"status","device":"esp32","ready":true}
{"type":"status","wiimote":1,"connected":false,"note":"press_1_and_2"}
{"type":"status","wiimote":1,"connected":false,"waiting":true}
{"type":"status","wiimote":1,"connected":true}
{"type":"btn","wiimote":1,"btn":"A","down":true}
{"type":"heartbeat","device":"esp32","wiimote":1,"connected":true,"battery":87}
{"type":"battery","wiimote":1,"level":87}
```

The add-on forwards all valid firmware messages to MQTT events topics and also publishes dedicated button, connection, heartbeat, and battery topics.

## Tested Environment

Known working setup in this repository:

- ESP32-WROOM-32 development board
- Nintendo Wii Remote
- Arduino ESP32 core `3.3.7`
- `arduino-cli`
- `ESP32Wiimote` library

## Requirements

You need:

- an ESP32 board with Bluetooth Classic support
- a USB data cable
- `arduino-cli` or the Arduino IDE
- Python 3 if you want to inspect serial output with `miniterm`
- the `ESP32Wiimote` library

## Firmware Location

The firmware lives here:

```text
esp32/
    wiimote-serial-bridge/
        wiimote-serial-bridge.ino
        include/
            buttons.h
            messages.h
            state.h
        src/
            buttons.cpp
            messages.cpp
```

Compile and upload from:

```bash
cd esp32/wiimote-serial-bridge
```

## Install `arduino-cli`

On Debian, Ubuntu, or WSL:

```bash
sudo apt update
sudo apt install -y curl
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
sudo mv bin/arduino-cli /usr/local/bin/
arduino-cli config init
arduino-cli core update-index
```

Confirm the tool is available:

```bash
arduino-cli version
```

## Install the ESP32 Core

Install the tested version:

```bash
arduino-cli core install esp32:esp32@3.3.7
```

Verify:

```bash
arduino-cli core list
```

You should see an entry that includes `esp32:esp32` and version `3.3.7`.

## Install the Wii Remote Library

If the library is available in your index, you can try:

```bash
arduino-cli lib install ESP32Wiimote
```

If that fails, install from GitHub instead:

```bash
arduino-cli lib install --git-url https://github.com/andremmfaria/ESP32Wiimote
```

Verify:

```bash
arduino-cli lib list | grep Wiimote
```

## Important Runtime Details

The firmware currently behaves like this:

- serial speed is `115200`
- Bluetooth library logging is set to warning level
- accelerometer and nunchuk stick data are filtered out
- the first post-connect button sample is used as a baseline
- heartbeat interval is 10 seconds
- waiting reminder interval is 5 seconds when disconnected
- battery refresh is requested every 60 seconds while connected

These values matter when you validate output against the Home Assistant add-on configuration.

## WSL USB Access

If you are using WSL, the ESP32 USB device must be attached to the Linux environment before flashing.

From Windows PowerShell:

```powershell
usbipd list
usbipd bind --busid <BUSID>
usbipd attach --wsl --busid <BUSID>
```

Then inside WSL:

```bash
ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

Typical result:

```text
/dev/ttyUSB0
```

## Compile the Firmware

From the firmware directory:

```bash
arduino-cli compile --fqbn esp32:esp32:esp32 .
```

Successful output ends with storage and memory usage summary lines.

## Upload the Firmware

Flash the board with:

```bash
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 .
```

Replace `/dev/ttyUSB0` with the correct serial device for your machine.

If upload fails:

1. Confirm the correct port.
2. Disconnect and reconnect the ESP32.
3. Hold the `BOOT` button during the beginning of the upload if your board requires it.
4. Make sure no serial monitor is already using the port.

## Verify Serial Output

To inspect the serial stream:

```bash
python3 -m serial.tools.miniterm /dev/ttyUSB0 115200
```

If your user lacks permission:

```bash
sudo python3 -m serial.tools.miniterm /dev/ttyUSB0 115200
```

Expected startup output is typically:

```json
{"type":"status","device":"esp32","ready":true}
{"type":"status","wiimote":1,"connected":false,"note":"press_1_and_2"}
{"type":"status","wiimote":1,"connected":false,"waiting":true}
```

## Pair the Wii Remote

With the serial monitor open:

1. Press `1 + 2` on the Wii Remote.
2. Wait for the connection status message.
3. Press a few buttons to verify live events.

Expected output once connected:

```json
{"type":"status","wiimote":1,"connected":true}
{"type":"btn","wiimote":1,"btn":"A","down":true}
{"type":"btn","wiimote":1,"btn":"A","down":false}
```

You may also see heartbeat and battery-related messages while connected.

## Button Names

The firmware currently emits these button identifiers:

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

## Common Problems

### `Library 'ESP32Wiimote@latest' not found`

Use the GitHub install form:

```bash
arduino-cli lib install --git-url https://github.com/andremmfaria/ESP32Wiimote
```

### `Permission denied` on the serial device

Either use `sudo` temporarily for validation or add your user to the appropriate device group for your distribution.

### Upload hangs or fails

Check:

1. The serial port is correct.
2. The USB cable carries data, not power only.
3. Another process is not holding the port open.
4. Your board does not require manual bootloader entry.

### No JSON output after flashing

Check:

1. The monitor is using `115200` baud.
2. The firmware actually uploaded to the correct board.
3. The board supports Bluetooth Classic.

## Next Step

Once the serial stream looks correct, continue with the add-on setup in `docs/ha-addon-setup.md`.
