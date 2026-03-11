from typing import Any

import paho.mqtt.client as mqtt

from ..transport.mqtt_client import publish_button, publish_connected, publish_heartbeat


def handle_message(client: mqtt.Client, topic_prefix: str, msg: dict[str, Any]) -> None:
    msg_type = msg.get("type")
    wiimote_id = int(msg.get("wiimote", 1))

    if msg_type == "btn":
        button = msg.get("btn")
        down = bool(msg.get("down", False))
        if isinstance(button, str) and button:
            publish_button(client, topic_prefix, wiimote_id, button, down)

    elif msg_type == "status":
        if "connected" in msg:
            publish_connected(client, topic_prefix, wiimote_id, bool(msg["connected"]))

    elif msg_type == "heartbeat":
        publish_heartbeat(client, topic_prefix, wiimote_id, msg)
