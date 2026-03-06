import json
import os
import signal
import sys
import time
from typing import Any

import paho.mqtt.client as mqtt
import serial


SERIAL_PORT = os.environ.get("SERIAL_PORT", "/dev/ttyUSB0")
SERIAL_BAUD = int(os.environ.get("SERIAL_BAUD", "115200"))
MQTT_HOST = os.environ.get("MQTT_HOST", "core-mosquitto")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")
TOPIC_PREFIX = os.environ.get("TOPIC_PREFIX", "wiimote")

RUNNING = True


def log(message: str) -> None:
    print(message, flush=True)


def handle_signal(signum: int, frame: Any) -> None:
    global RUNNING
    log(f"Received signal {signum}, shutting down")
    RUNNING = False


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


def mqtt_connect() -> mqtt.Client:
    client = mqtt.Client(client_id="wiimote-serial-bridge", clean_session=True)

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()
    log(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
    return client


def mqtt_publish(client: mqtt.Client, topic: str, payload: str, retain: bool = False) -> None:
    result = client.publish(topic, payload, retain=retain)
    result.wait_for_publish()
    log(f"MQTT {topic} -> {payload}")


def publish_button(client: mqtt.Client, wiimote_id: int, button: str, down: bool) -> None:
    topic = f"{TOPIC_PREFIX}/{wiimote_id}/button/{button}"
    payload = "ON" if down else "OFF"
    mqtt_publish(client, topic, payload, retain=False)


def publish_connected(client: mqtt.Client, wiimote_id: int, connected: bool) -> None:
    topic = f"{TOPIC_PREFIX}/{wiimote_id}/status/connected"
    payload = "true" if connected else "false"
    mqtt_publish(client, topic, payload, retain=True)


def publish_heartbeat(client: mqtt.Client, wiimote_id: int, payload_obj: dict[str, Any]) -> None:
    topic = f"{TOPIC_PREFIX}/{wiimote_id}/status/heartbeat"
    payload = json.dumps(payload_obj, separators=(",", ":"))
    mqtt_publish(client, topic, payload, retain=False)


def handle_message(client: mqtt.Client, msg: dict[str, Any]) -> None:
    msg_type = msg.get("type")
    wiimote_id = int(msg.get("wiimote", 1))

    if msg_type == "btn":
        button = msg.get("btn")
        down = bool(msg.get("down", False))
        if isinstance(button, str) and button:
            publish_button(client, wiimote_id, button, down)

    elif msg_type == "status":
        if "connected" in msg:
            publish_connected(client, wiimote_id, bool(msg["connected"]))

    elif msg_type == "heartbeat":
        publish_heartbeat(client, wiimote_id, msg)


def open_serial() -> serial.Serial:
    log(f"Opening serial port {SERIAL_PORT} at {SERIAL_BAUD} baud")
    return serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)


def main() -> int:
    client = mqtt_connect()
    ser = None

    try:
        while RUNNING:
            if ser is None:
                try:
                    ser = open_serial()
                except Exception as exc:
                    log(f"Serial open failed: {exc}")
                    time.sleep(5)
                    continue

            try:
                line = ser.readline()
                if not line:
                    continue

                text = line.decode(errors="ignore").strip()
                if not text:
                    continue

                log(f"SERIAL {text}")

                if not text.startswith("{"):
                    continue

                try:
                    msg = json.loads(text)
                except json.JSONDecodeError:
                    log("Skipping invalid JSON line")
                    continue

                if isinstance(msg, dict):
                    handle_message(client, msg)

            except serial.SerialException as exc:
                log(f"Serial error: {exc}")
                try:
                    ser.close()
                except Exception:
                    pass
                ser = None
                time.sleep(2)

            except Exception as exc:
                log(f"Unexpected error while processing serial data: {exc}")
                time.sleep(1)

    finally:
        if ser is not None:
            try:
                ser.close()
            except Exception:
                pass

        try:
            client.loop_stop()
            client.disconnect()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
