import json
from collections.abc import Iterable
from typing import Any

import paho.mqtt.client as mqtt

from .constants import WIIMOTE_BUTTONS
from .publish import message
from .types import DiscoveryStats


def configs(
    client: mqtt.Client,
    topic_prefix: str,
    wiimote_ids: Iterable[int],
    discovery_prefix: str = "homeassistant",
) -> DiscoveryStats:
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
    return message(client, topic, payload, retain=True)
