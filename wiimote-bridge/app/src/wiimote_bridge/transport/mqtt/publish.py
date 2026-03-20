import json
import time
from typing import Any

import paho.mqtt.client as mqtt

from wiimote_bridge.utils.logging import get_logger
from wiimote_bridge.utils.types import MessagePayload

LOGGER = get_logger(__name__)
PUBLISH_WARNING_INTERVAL_SECONDS = 15.0
_last_publish_warning_at: float | None = None


def _warn_publish_issue(message: str, *args: Any) -> None:
    global _last_publish_warning_at

    now = time.monotonic()
    if (
        _last_publish_warning_at is None
        or (now - _last_publish_warning_at) >= PUBLISH_WARNING_INTERVAL_SECONDS
    ):
        LOGGER.warning(message, *args)
        _last_publish_warning_at = now


def message(
    client: mqtt.Client, topic: str, payload: str, retain: bool = False
) -> bool:
    if hasattr(client, "is_connected") and not client.is_connected():
        _warn_publish_issue(
            "Skipping MQTT publish while client is disconnected: %s", topic
        )
        return False

    result = client.publish(topic, payload, retain=retain)

    if getattr(result, "rc", mqtt.MQTT_ERR_SUCCESS) != mqtt.MQTT_ERR_SUCCESS:
        _warn_publish_issue(
            "Skipping MQTT publish to %s: %s", topic, mqtt.error_string(result.rc)
        )
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


def _normalize_wiimote_payload(
    payload_obj: MessagePayload, wiimote_id: int
) -> MessagePayload:
    if "wiimote" not in payload_obj:
        return payload_obj

    normalized_payload = dict(payload_obj)
    normalized_payload["wiimote"] = wiimote_id
    return normalized_payload


def event_message(
    client: mqtt.Client, topic_prefix: str, wiimote_id: int, payload_obj: MessagePayload
) -> None:
    msg_type = str(payload_obj.get("type", "unknown"))

    if "wiimote" in payload_obj:
        topic = f"{topic_prefix}/{wiimote_id}/events/{msg_type}"
        payload_obj = _normalize_wiimote_payload(payload_obj, wiimote_id)
    else:
        device = str(payload_obj.get("device", "bridge"))
        topic = f"{topic_prefix}/device/{device}/events/{msg_type}"

    payload = json.dumps(payload_obj, separators=(",", ":"))

    message(client, topic, payload, retain=False)


def button(
    client: mqtt.Client, topic_prefix: str, wiimote_id: int, button: str, down: bool
) -> None:
    topic = f"{topic_prefix}/{wiimote_id}/button/{button}"
    payload = "ON" if down else "OFF"
    message(client, topic, payload, retain=False)


def connected(
    client: mqtt.Client, topic_prefix: str, wiimote_id: int, connected: bool
) -> None:
    topic = f"{topic_prefix}/{wiimote_id}/status/connected"
    payload = "true" if connected else "false"
    message(client, topic, payload, retain=True)


def battery(
    client: mqtt.Client, topic_prefix: str, wiimote_id: int, level: int
) -> None:
    topic = f"{topic_prefix}/{wiimote_id}/status/battery"
    message(client, topic, str(level), retain=True)


def heartbeat(
    client: mqtt.Client, topic_prefix: str, wiimote_id: int, payload_obj: MessagePayload
) -> None:
    topic = f"{topic_prefix}/{wiimote_id}/status/heartbeat"
    payload = json.dumps(
        _normalize_wiimote_payload(payload_obj, wiimote_id), separators=(",", ":")
    )
    message(client, topic, payload, retain=False)
