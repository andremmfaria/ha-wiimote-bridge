import json
import signal
import threading
from typing import Any

import serial

from wiimote_bridge.core.handlers import handle_message
from wiimote_bridge.transport.mqtt_client import connect_mqtt_with_discovery
from wiimote_bridge.transport.serial_reader import open_serial
from wiimote_bridge.utils.config import RadioConfig, load_settings
from wiimote_bridge.utils.logging import configure_logging, get_logger


LOGGER = get_logger(__name__)


def run_radio(
    radio: RadioConfig,
    client: Any,
    topic_prefix: str,
    stop_event: threading.Event,
) -> None:
    radio_logger = get_logger(f"wiimote_bridge.radio.{radio.controller_id}")
    ser = None
    try:
        while not stop_event.is_set():
            if ser is None:
                try:
                    ser = open_serial(radio.port, radio.baud)
                    radio_logger.info("Serial connection established on %s", radio.port)
                except Exception as exc:
                    radio_logger.error("Serial open failed on %s: %s", radio.port, exc)
                    stop_event.wait(5)
                    continue

            try:
                line = ser.readline()
                if not line:
                    continue

                text = line.decode(errors="ignore").strip()
                if not text:
                    continue

                radio_logger.info("SERIAL %s", text)

                if not text.startswith("{"):
                    radio_logger.debug("Skipping non-JSON serial line")
                    continue

                try:
                    msg = json.loads(text)
                except json.JSONDecodeError:
                    radio_logger.warning("Skipping invalid JSON line")
                    continue

                if isinstance(msg, dict):
                    handle_message(client, topic_prefix, radio.controller_id, msg)

            except serial.SerialException as exc:
                radio_logger.error("Serial error on %s: %s", radio.port, exc)
                try:
                    ser.close()
                except Exception:
                    pass
                ser = None
                stop_event.wait(2)

            except Exception as exc:
                radio_logger.exception(
                    "Unexpected error while processing serial data on %s: %s",
                    radio.port,
                    exc,
                )
                stop_event.wait(1)

    finally:
        if ser is not None:
            try:
                ser.close()
            except Exception:
                pass


def run() -> int:
    settings = load_settings()
    configured_log_level = configure_logging(settings.log_level)

    LOGGER.info("Starting WiiMote Bridge application")
    LOGGER.info("Log level: %s", configured_log_level.upper())
    for radio in settings.radios:
        LOGGER.info(
            "Radio: %s @ %s baud, controller ID %s",
            radio.port,
            radio.baud,
            radio.controller_id,
        )
    LOGGER.info("MQTT broker: %s:%s", settings.mqtt_host, settings.mqtt_port)
    LOGGER.debug("MQTT username configured: %s", bool(settings.mqtt_username))
    LOGGER.info("MQTT transport: %s", settings.mqtt_transport)
    LOGGER.info("MQTT SSL enabled: %s", settings.mqtt_ssl)
    LOGGER.info("MQTT SSL insecure cert verification: %s", settings.mqtt_ssl_insecure)
    LOGGER.debug("Topic prefix: %s", settings.topic_prefix)
    LOGGER.debug("MQTT discovery enabled: %s", settings.discover_enabled)

    stop_event = threading.Event()

    def handle_signal(signum: int, frame: Any) -> None:
        del frame
        LOGGER.info("Received signal %s, shutting down", signum)
        stop_event.set()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    controller_ids = tuple(radio.controller_id for radio in settings.radios)
    client = connect_mqtt_with_discovery(
        settings,
        discovery_enabled=settings.discover_enabled,
        discovery_topic_prefix=settings.topic_prefix,
        discovery_wiimote_ids=controller_ids,
    )

    threads = [
        threading.Thread(
            target=run_radio,
            args=(radio, client, settings.topic_prefix, stop_event),
            daemon=True,
            name=f"radio-{radio.controller_id}",
        )
        for radio in settings.radios
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    try:
        client.loop_stop()
        client.disconnect()
        LOGGER.info("MQTT client disconnected")
    except Exception:
        pass

    return 0
