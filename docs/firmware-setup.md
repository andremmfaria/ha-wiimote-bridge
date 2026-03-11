# Firmware Setup

This guide explains how to build and flash the ESP32 firmware for the WiiMote Bridge project.

The firmware connects to a Nintendo Wii Remote over Bluetooth and emits JSON events over USB serial.

---

# Tested Environment

This setup was tested with:

- ESP32-WROOM-32 development board ([link](https://www.amazon.co.uk/dp/B0DGLCWR76))
- Nintendo Wii Remote
- `arduino-cli`
- WSL on Windows
- Arduino ESP32 core `3.3.7`
- `ESP32Wiimote` library

---

# Requirements

You need:

* an ESP32 board with Bluetooth Classic support
* a USB cable
* `arduino-cli`
* Python 3
* The `ESP32Wiimote` library

---

# Install arduino-cli

On Debian, Ubuntu, or WSL:

```bash
sudo apt update
sudo apt install curl
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
sudo mv bin/arduino-cli /usr/local/bin/
```

Initialize the config:

```bash
arduino-cli config init
arduino-cli core update-index
```

---

# Install the ESP32 Core

Install the tested version:

```bash
arduino-cli core install esp32:esp32@3.3.7
```

Verify:

```bash
arduino-cli core list
```

Expected output should include:

```text
esp32:esp32 3.3.7
```

---

# Install the Wiimote Library

Install directly from GitHub:

```bash
arduino-cli lib install ESP32Wiimote`
```

You can confirm installation with:

```bash
arduino-cli lib list | grep Wiimote
```

---

# Repository Layout

The firmware is located here:

```text
esp32/
└── wiimote_serial_bridge/
    └── wiimote_serial_bridge.ino
```

Change into that directory before compiling:

```bash
cd esp32/wiimote_serial_bridge
```

---

# USB Access in WSL

If you are using WSL, the ESP32 USB device must be attached to WSL before you can flash it.

First, on Windows, list USB devices:

```powershell
usbipd list
```

Bind the ESP32 device:

```powershell
usbipd bind --busid <BUSID>
```

Attach it to WSL:

```powershell
usbipd attach --wsl --busid <BUSID>
```

Then inside WSL, confirm the serial device exists:

```bash
ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

Typical result:

```text
/dev/ttyUSB0
```

---

# Compile the Firmware

From the firmware directory:

```bash
arduino-cli compile --fqbn esp32:esp32:esp32 .
```

A successful build will end with output similar to:

```text
Sketch uses ... bytes of program storage space.
Global variables use ... bytes of dynamic memory.
```

---

# Upload the Firmware

Flash the ESP32:

```bash
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 .
```

Replace `/dev/ttyUSB0` with your actual port if needed.

If flashing fails, try pressing and holding the **BOOT** button on the ESP32 during the start of the upload.

---

# Monitor Serial Output

To verify the firmware is running:

```bash
python3 -m serial.tools.miniterm /dev/ttyUSB0 115200
```

If your user does not have permission for the serial device, use:

```bash
sudo python3 -m serial.tools.miniterm /dev/ttyUSB0 115200
```

You should see output similar to:

```text
{"type":"status","device":"esp32","ready":true}
{"type":"status","wiimote":1,"connected":false,"note":"press_1_and_2"}
{"type":"status","wiimote":1,"connected":false,"waiting":true}
```

---

# Pair the Wii Remote

Once the firmware is running:

1. Keep the serial monitor open
2. Press **1 + 2** on the Wii Remote
3. Wait for the ESP32 to connect

When pairing succeeds, you should see:

```text
{"type":"status","wiimote":1,"connected":true}
```

Then press buttons on the Wii Remote. You should see events such as:

```text
{"type":"btn","wiimote":1,"btn":"A","down":true}
{"type":"btn","wiimote":1,"btn":"A","down":false}
{"type":"btn","wiimote":1,"btn":"PLUS","down":true}
{"type":"btn","wiimote":1,"btn":"PLUS","down":false}
```

---

# Heartbeat Messages

The firmware emits periodic heartbeat messages to confirm it is still alive.

Example:

```text
{"type":"heartbeat","device":"esp32","wiimote":1,"connected":true}
```

These are used by the Home Assistant bridge for health monitoring.

---

# Common Problems

## `Library 'ESP32Wiimote@latest' not found`

Cause:

* library is not available in the normal Arduino library index

Fix:

* install from GitHub instead

```bash
arduino-cli lib install --git-url https://github.com/andremmfaria/ESP32Wiimote
```

---

## `Permission denied: '/dev/ttyUSB0'`

Cause:

* current user cannot access the serial device

Fix:

* run the serial monitor with `sudo`
* or add your user to the appropriate serial device group

Example:

```bash
sudo python3 -m serial.tools.miniterm /dev/ttyUSB0 115200
```

---

## Upload fails

Possible fixes:

* confirm the correct serial port
* unplug and reconnect the ESP32
* hold the **BOOT** button during upload
* make sure no serial monitor is already using the port

---

# Next Step

Once the firmware is working and serial JSON output is confirmed, continue with the Home Assistant add-on setup.
