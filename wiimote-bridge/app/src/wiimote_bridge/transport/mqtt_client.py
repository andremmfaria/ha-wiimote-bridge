import json
import time
from typing import Any

import paho.mqtt.client as mqtt

from wiimote_bridge.utils.config import Settings
from wiimote_bridge.utils.logging import get_logger


LOGGER = get_logger(__name__)
PUBLISH_WARNING_INTERVAL_SECONDS = 15.0
_last_publish_warning_at: float | None = None


def _warn_publish_issue(message: str, *args: Any) -> None:
    global _last_publish_warning_at

    now = time.monotonic()
    if _last_publish_warning_at is None or (now - _last_publish_warning_at) >= PUBLISH_WARNING_INTERVAL_SECONDS:
        LOGGER.warning(message, *args)
        _last_publish_warning_at = now


def connect_mqtt(settings: Settings) -> mqtt.Client:
    client = mqtt.Client(client_id="wiimote-serial-bridge", clean_session=True)

    def on_connect(_client, _userdata, _flags, reason_code, _properties=None) -> None:
        if reason_code == 0:
            LOGGER.info("Connected to MQTT broker at %s:%s", settings.mqtt_host, settings.mqtt_port)
            return

        LOGGER.warning("MQTT connection failed: %s", mqtt.error_string(reason_code))

    def on_disconnect(_client, _userdata, _disconnect_flags, reason_code, _properties=None) -> None:
        if reason_code == 0:
            LOGGER.info("MQTT client disconnected")
            return

        LOGGER.warning("MQTT client disconnected: %s", mqtt.error_string(reason_code))

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


def publish_event_message(client: mqtt.Client, topic_prefix: str, payload_obj: dict[str, Any]) -> None:
    msg_type = str(payload_obj.get("type", "unknown"))
    payload = json.dumps(payload_obj, separators=(",", ":"))

    if "wiimote" in payload_obj:
        topic = f"{topic_prefix}/{int(payload_obj['wiimote'])}/events/{msg_type}"
    else:
        device = str(payload_obj.get("device", "bridge"))
        topic = f"{topic_prefix}/device/{device}/events/{msg_type}"

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
    payload = json.dumps(payload_obj, separators=(",", ":"))
    mqtt_publish(client, topic, payload, retain=False)
