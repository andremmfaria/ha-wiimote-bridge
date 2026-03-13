import json
from typing import Any

import paho.mqtt.client as mqtt

from wiimote_bridge.utils.config import Settings
from wiimote_bridge.utils.logging import get_logger


LOGGER = get_logger(__name__)


def connect_mqtt(settings: Settings) -> mqtt.Client:
    client = mqtt.Client(client_id="wiimote-serial-bridge", clean_session=True)

    if settings.mqtt_username:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

    client.connect(settings.mqtt_host, settings.mqtt_port, 60)
    client.loop_start()
    LOGGER.info("Connected to MQTT broker at %s:%s", settings.mqtt_host, settings.mqtt_port)
    return client


def mqtt_publish(client: mqtt.Client, topic: str, payload: str, retain: bool = False) -> None:
    result = client.publish(topic, payload, retain=retain)
    result.wait_for_publish()
    LOGGER.info("MQTT %s -> %s", topic, payload)


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
