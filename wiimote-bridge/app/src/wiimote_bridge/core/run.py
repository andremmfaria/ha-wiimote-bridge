import json
import signal
import time
from typing import Any

import serial

from wiimote_bridge.core.handlers import handle_message
from wiimote_bridge.transport.mqtt_client import connect_mqtt
from wiimote_bridge.transport.serial_reader import open_serial
from wiimote_bridge.utils.config import load_settings
from wiimote_bridge.utils.logging import get_logger


LOGGER = get_logger(__name__)


def run() -> int:
    settings = load_settings()
    running = True

    def handle_signal(signum: int, frame: Any) -> None:
        nonlocal running
        del frame
        LOGGER.info("Received signal %s, shutting down", signum)
        running = False

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    client = connect_mqtt(settings)
    ser = None

    try:
        while running:
            if ser is None:
                try:
                    ser = open_serial(settings)
                except Exception as exc:
                    LOGGER.error("Serial open failed: %s", exc)
                    time.sleep(5)
                    continue

            try:
                line = ser.readline()
                if not line:
                    continue

                text = line.decode(errors="ignore").strip()
                if not text:
                    continue

                LOGGER.info("SERIAL %s", text)

                if not text.startswith("{"):
                    continue

                try:
                    msg = json.loads(text)
                except json.JSONDecodeError:
                    LOGGER.warning("Skipping invalid JSON line")
                    continue

                if isinstance(msg, dict):
                    handle_message(client, settings.topic_prefix, msg)

            except serial.SerialException as exc:
                LOGGER.error("Serial error: %s", exc)
                try:
                    ser.close()
                except Exception:
                    pass
                ser = None
                time.sleep(2)

            except Exception as exc:
                LOGGER.exception("Unexpected error while processing serial data: %s", exc)
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
