import json
import ssl
import time
from collections.abc import Iterable
from typing import Any

import paho.mqtt.client as mqtt

from wiimote_bridge.utils.config import Settings
from wiimote_bridge.utils.logging import get_logger


LOGGER = get_logger(__name__)
PUBLISH_WARNING_INTERVAL_SECONDS = 15.0
_last_publish_warning_at: float | None = None
WIIMOTE_BUTTONS = ("A", "B", "UP", "DOWN", "LEFT", "RIGHT", "PLUS", "MINUS", "HOME", "ONE", "TWO")


def _warn_publish_issue(message: str, *args: Any) -> None:
    global _last_publish_warning_at

    now = time.monotonic()
    if _last_publish_warning_at is None or (now - _last_publish_warning_at) >= PUBLISH_WARNING_INTERVAL_SECONDS:
        LOGGER.warning(message, *args)
        _last_publish_warning_at = now


def connect_mqtt(settings: Settings) -> mqtt.Client:
    return connect_mqtt_with_discovery(
        settings,
        discovery_enabled=False,
        discovery_topic_prefix=settings.topic_prefix,
        discovery_wiimote_ids=(),
    )


def connect_mqtt_with_discovery(
    settings: Settings,
    *,
    discovery_enabled: bool,
    discovery_topic_prefix: str,
    discovery_wiimote_ids: Iterable[int],
    discovery_prefix: str = "homeassistant",
) -> mqtt.Client:
    wiimote_ids = tuple(int(wiimote_id) for wiimote_id in discovery_wiimote_ids)

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="wiimote-serial-bridge",
        clean_session=True,
        transport=settings.mqtt_transport,
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
            LOGGER.info("Connected to MQTT broker at %s:%s", settings.mqtt_host, settings.mqtt_port)
            if not discovery_enabled:
                LOGGER.info("MQTT discovery publishing is disabled")
                return

            if not wiimote_ids:
                LOGGER.warning("MQTT discovery enabled but no controller IDs are configured")
                return

            expected_entities = len(wiimote_ids) * (2 + len(WIIMOTE_BUTTONS))
            LOGGER.info(
                "Publishing MQTT discovery for %s controller(s); expecting %s entity configs",
                len(wiimote_ids),
                expected_entities,
            )
            result = publish_discovery_configs(
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
            return

        LOGGER.warning("MQTT connection failed: %s", mqtt.error_string(reason_code_value))

    def on_disconnect(_client, _userdata, _disconnect_flags, reason_code, _properties=None) -> None:
        reason_code_value = _reason_code_value(reason_code)

        if reason_code_value == 0:
            LOGGER.info("MQTT client disconnected")
            return

        LOGGER.warning("MQTT client disconnected: %s", mqtt.error_string(reason_code_value))

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    if settings.mqtt_username:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

    client.connect(settings.mqtt_host, settings.mqtt_port, 60)
    client.loop_start()
    return client


def mqtt_publish(client: mqtt.Client, topic: str, payload: str, retain: bool = False) -> bool:
    if hasattr(client, "is_connected") and not client.is_connected():
        _warn_publish_issue("Skipping MQTT publish while client is disconnected: %s", topic)
        return False

    result = client.publish(topic, payload, retain=retain)

    if getattr(result, "rc", mqtt.MQTT_ERR_SUCCESS) != mqtt.MQTT_ERR_SUCCESS:
        _warn_publish_issue("Skipping MQTT publish to %s: %s", topic, mqtt.error_string(result.rc))
        return False

    try:
        result.wait_for_publish()
    except RuntimeError as exc:
        _warn_publish_issue(
            "Skipping MQTT publish to %s because the client is disconnected: %s",
            topic,
            exc,
        )
        return False

    LOGGER.info("MQTT %s -> %s", topic, payload)
    return True


def _normalize_wiimote_payload(payload_obj: dict[str, Any], wiimote_id: int) -> dict[str, Any]:
    if "wiimote" not in payload_obj:
        return payload_obj

    normalized_payload = dict(payload_obj)
    normalized_payload["wiimote"] = wiimote_id
    return normalized_payload


def publish_event_message(client: mqtt.Client, topic_prefix: str, wiimote_id: int, payload_obj: dict[str, Any]) -> None:
    msg_type = str(payload_obj.get("type", "unknown"))

    if "wiimote" in payload_obj:
        topic = f"{topic_prefix}/{wiimote_id}/events/{msg_type}"
        payload_obj = _normalize_wiimote_payload(payload_obj, wiimote_id)
    else:
        device = str(payload_obj.get("device", "bridge"))
        topic = f"{topic_prefix}/device/{device}/events/{msg_type}"

    payload = json.dumps(payload_obj, separators=(",", ":"))

    mqtt_publish(client, topic, payload, retain=False)


def publish_button(client: mqtt.Client, topic_prefix: str, wiimote_id: int, button: str, down: bool) -> None:
    topic = f"{topic_prefix}/{wiimote_id}/button/{button}"
    payload = "ON" if down else "OFF"
    mqtt_publish(client, topic, payload, retain=False)


def publish_connected(client: mqtt.Client, topic_prefix: str, wiimote_id: int, connected: bool) -> None:
    topic = f"{topic_prefix}/{wiimote_id}/status/connected"
    payload = "true" if connected else "false"
    mqtt_publish(client, topic, payload, retain=True)


def publish_battery(client: mqtt.Client, topic_prefix: str, wiimote_id: int, level: int) -> None:
    topic = f"{topic_prefix}/{wiimote_id}/status/battery"
    mqtt_publish(client, topic, str(level), retain=True)


def publish_heartbeat(client: mqtt.Client, topic_prefix: str, wiimote_id: int, payload_obj: dict[str, Any]) -> None:
    topic = f"{topic_prefix}/{wiimote_id}/status/heartbeat"
    payload = json.dumps(_normalize_wiimote_payload(payload_obj, wiimote_id), separators=(",", ":"))
    mqtt_publish(client, topic, payload, retain=False)


def publish_discovery_configs(
    client: mqtt.Client,
    topic_prefix: str,
    wiimote_ids: Iterable[int],
    discovery_prefix: str = "homeassistant",
) -> dict[str, int]:
    controllers = 0
    entities = 0
    failed = 0

    for wiimote_id in wiimote_ids:
        announced, failed_for_controller = _publish_controller_discovery(
            client,
            topic_prefix,
            int(wiimote_id),
            discovery_prefix,
        )
        controllers += 1
        entities += announced
        failed += failed_for_controller

    return {
        "controllers": controllers,
        "entities": entities,
        "failed": failed,
    }


def _publish_controller_discovery(
    client: mqtt.Client,
    topic_prefix: str,
    wiimote_id: int,
    discovery_prefix: str,
) -> tuple[int, int]:
    announced = 0
    failed = 0

    device_id = f"wiimote_bridge_{wiimote_id}"
    device_name = f"WiiMote {wiimote_id}"
    object_prefix = f"wiimote_{wiimote_id}"
    device = {
        "identifiers": [device_id],
        "name": device_name,
        "manufacturer": "Nintendo",
        "model": "Wii Remote",
    }

    connected_cfg = {
        "name": "Connected",
        "unique_id": f"{device_id}_connected",
        "state_topic": f"{topic_prefix}/{wiimote_id}/status/connected",
        "payload_on": "true",
        "payload_off": "false",
        "device_class": "connectivity",
        "entity_category": "diagnostic",
        "device": device,
    }
    if _publish_discovery_entity(
        client,
        discovery_prefix,
        "binary_sensor",
        object_prefix,
        "connected",
        connected_cfg,
    ):
        announced += 1
    else:
        failed += 1

    battery_cfg = {
        "name": "Battery",
        "unique_id": f"{device_id}_battery",
        "state_topic": f"{topic_prefix}/{wiimote_id}/status/battery",
        "unit_of_measurement": "%",
        "device_class": "battery",
        "state_class": "measurement",
        "entity_category": "diagnostic",
        "device": device,
    }
    if _publish_discovery_entity(
        client,
        discovery_prefix,
        "sensor",
        object_prefix,
        "battery",
        battery_cfg,
    ):
        announced += 1
    else:
        failed += 1

    for button in WIIMOTE_BUTTONS:
        button_cfg = {
            "name": button,
            "unique_id": f"{device_id}_button_{button.lower()}",
            "state_topic": f"{topic_prefix}/{wiimote_id}/button/{button}",
            "payload_on": "ON",
            "payload_off": "OFF",
            "device": device,
        }
        if _publish_discovery_entity(
            client,
            discovery_prefix,
            "binary_sensor",
            object_prefix,
            f"button_{button.lower()}",
            button_cfg,
        ):
            announced += 1
        else:
            failed += 1

    return announced, failed


def _publish_discovery_entity(
    client: mqtt.Client,
    discovery_prefix: str,
    component: str,
    object_prefix: str,
    object_id: str,
    config_payload: dict[str, Any],
) -> bool:
    topic = f"{discovery_prefix}/{component}/{object_prefix}/{object_id}/config"
    payload = json.dumps(config_payload, separators=(",", ":"))
    return mqtt_publish(client, topic, payload, retain=True)
