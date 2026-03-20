import hashlib
import json
import os
import signal
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import serial

from wiimote_bridge.core.handlers import handle_message
from wiimote_bridge.transport.mqtt.connection import connect_with_discovery
from wiimote_bridge.transport.serial_reader import open_serial
from wiimote_bridge.utils.config import RadioConfig, load_settings
from wiimote_bridge.utils.logging import configure_logging, get_logger

LOGGER = get_logger(__name__)
OPTIONS_PATH = "/data/options.json"
CONFIG_CHANGED_EXIT_CODE = 75


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/health", "/health/"}:
            body = b"ok\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        del format, args
        return


def _start_health_server(port: int) -> ThreadingHTTPServer | None:
    if port <= 0:
        return None

    try:
        server = ThreadingHTTPServer(("0.0.0.0", port), _HealthHandler)
    except OSError as exc:
        LOGGER.warning("Health endpoint failed to bind on port %s: %s", port, exc)
        return None

    thread = threading.Thread(
        target=server.serve_forever,
        kwargs={"poll_interval": 0.5},
        daemon=True,
        name="health-server",
    )
    thread.start()
    LOGGER.info("Health endpoint listening on 0.0.0.0:%s/health", port)
    return server


def _fingerprint_file(path: str) -> str | None:
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except FileNotFoundError:
        return None


class _ConfigChangeWatcher:
    def __init__(
        self, path: str, stop_event: threading.Event, poll_interval: float = 2.0
    ) -> None:
        self._path = path
        self._stop_event = stop_event
        self._poll_interval = poll_interval
        self._baseline = _fingerprint_file(path)
        self._changed = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def enabled(self) -> bool:
        return self._baseline is not None

    @property
    def changed(self) -> bool:
        return self._changed.is_set()

    def start(self) -> None:
        if not self.enabled:
            return

        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="config-watch",
        )
        self._thread.start()

    def _run(self) -> None:
        while not self._stop_event.wait(self._poll_interval):
            current = _fingerprint_file(self._path)
            if current is None or current == self._baseline:
                continue

            LOGGER.warning(
                "Detected add-on config change at %s; forcing restart to apply updated options",
                self._path,
            )
            self._changed.set()
            self._stop_event.set()
            return


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
    LOGGER.info("Health endpoint port: %s", settings.health_port)

    stop_event = threading.Event()
    options_path = os.environ.get("WIIMOTE_BRIDGE_OPTIONS_PATH", OPTIONS_PATH)
    config_watcher = _ConfigChangeWatcher(options_path, stop_event)

    def handle_signal(signum: int, frame: Any) -> None:
        del frame
        LOGGER.info("Received signal %s, shutting down", signum)
        stop_event.set()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    health_server = _start_health_server(settings.health_port)

    if config_watcher.enabled:
        LOGGER.info("Watching add-on options for changes: %s", options_path)
        config_watcher.start()
    else:
        LOGGER.debug(
            "Options file not found; config change watcher disabled for %s",
            options_path,
        )

    controller_ids = tuple(radio.controller_id for radio in settings.radios)
    client = connect_with_discovery(
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

    if health_server is not None:
        try:
            health_server.shutdown()
            health_server.server_close()
            LOGGER.info("Health endpoint stopped")
        except Exception:
            pass

    if config_watcher.changed:
        LOGGER.warning(
            "Exiting with code %s so the supervisor restarts the add-on",
            CONFIG_CHANGED_EXIT_CODE,
        )
        return CONFIG_CHANGED_EXIT_CODE

    return 0
