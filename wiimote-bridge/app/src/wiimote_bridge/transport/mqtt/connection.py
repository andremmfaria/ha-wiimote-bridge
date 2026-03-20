import ssl
import threading
from collections.abc import Iterable
from typing import Any

import paho.mqtt.client as mqtt

from wiimote_bridge.utils.config import Settings
from wiimote_bridge.utils.logging import get_logger
from wiimote_bridge.utils.types import MqttTransport

from .constants import WIIMOTE_BUTTONS
from .discovery import configs
from .errors import (_describe_connect_exception, _describe_connect_reason,
                     _describe_disconnect_reason, _format_mqtt_failure)

LOGGER = get_logger(__name__)


def connect(settings: Settings) -> mqtt.Client:
    return connect_with_discovery(
        settings,
        discovery_enabled=False,
        discovery_topic_prefix=settings.topic_prefix,
        discovery_wiimote_ids=(),
    )


def connect_with_discovery(
    settings: Settings,
    *,
    discovery_enabled: bool,
    discovery_topic_prefix: str,
    discovery_wiimote_ids: Iterable[int],
    discovery_prefix: str = "homeassistant",
) -> mqtt.Client:
    wiimote_ids = tuple(int(wiimote_id) for wiimote_id in discovery_wiimote_ids)
    transport: MqttTransport = settings.mqtt_transport

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="wiimote-serial-bridge",
        clean_session=True,
        transport=transport,
    )

    LOGGER.info("MQTT transport mode: %s", settings.mqtt_transport)
    if settings.mqtt_ssl:
        cert_reqs = ssl.CERT_NONE if settings.mqtt_ssl_insecure else ssl.CERT_REQUIRED
        client.tls_set(cert_reqs=cert_reqs)
        client.tls_insecure_set(settings.mqtt_ssl_insecure)
        LOGGER.info("MQTT TLS enabled")
        if settings.mqtt_ssl_insecure:
            LOGGER.warning("MQTT TLS certificate verification is disabled")

    def _reason_code_value(reason_code: Any) -> int:
        if isinstance(reason_code, int):
            return reason_code

        value = getattr(reason_code, "value", None)
        if isinstance(value, int):
            return value

        try:
            return int(reason_code)
        except (TypeError, ValueError):
            return mqtt.MQTT_ERR_UNKNOWN

    def on_connect(_client, _userdata, _flags, reason_code, _properties=None) -> None:
        reason_code_value = _reason_code_value(reason_code)

        if reason_code_value == 0:
            LOGGER.info(
                "Connected to MQTT broker at %s:%s",
                settings.mqtt_host,
                settings.mqtt_port,
            )
            if not discovery_enabled:
                LOGGER.info("MQTT discovery publishing is disabled")
                return

            if not wiimote_ids:
                LOGGER.warning(
                    "MQTT discovery enabled but no controller IDs are configured"
                )
                return

            expected_entities = len(wiimote_ids) * (2 + len(WIIMOTE_BUTTONS))
            LOGGER.info(
                "Publishing MQTT discovery for %s controller(s); expecting %s entity configs",
                len(wiimote_ids),
                expected_entities,
            )

            def _run_discovery() -> None:
                result = configs(
                    client,
                    discovery_topic_prefix,
                    wiimote_ids,
                    discovery_prefix=discovery_prefix,
                )
                if result["failed"] > 0:
                    LOGGER.warning(
                        "MQTT discovery publish completed with failures: %s/%s entities failed",
                        result["failed"],
                        result["entities"],
                    )
                else:
                    LOGGER.info(
                        "MQTT discovery publish completed successfully: %s entities announced",
                        result["entities"],
                    )

            threading.Thread(
                target=_run_discovery, daemon=True, name="mqtt-discovery"
            ).start()
            return

        LOGGER.warning(
            "MQTT connection failed: %s",
            _format_mqtt_failure(_describe_connect_reason(reason_code), settings),
        )

    def on_disconnect(
        _client, _userdata, _disconnect_flags, reason_code, _properties=None
    ) -> None:
        reason_code_value = _reason_code_value(reason_code)

        if reason_code_value == 0:
            LOGGER.info("MQTT client disconnected")
            return

        LOGGER.warning(
            "MQTT client disconnected: %s",
            _format_mqtt_failure(_describe_disconnect_reason(reason_code), settings),
        )

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    if settings.mqtt_username:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

    try:
        client.connect(settings.mqtt_host, settings.mqtt_port, 60)
    except Exception as exc:
        LOGGER.warning(
            "MQTT initial connect failed: %s",
            _format_mqtt_failure(_describe_connect_exception(exc, settings), settings),
        )
        raise

    client.loop_start()
    return client
