import paho.mqtt.client as mqtt

from wiimote_bridge.transport.mqtt_client import (
    publish_battery,
    publish_button,
    publish_connected,
    publish_event_message,
    publish_heartbeat,
)
from wiimote_bridge.utils.types import MessagePayload


def handle_message(client: mqtt.Client, topic_prefix: str, wiimote_id: int, msg: MessagePayload) -> None:
    msg_type = msg.get("type")

    publish_event_message(client, topic_prefix, wiimote_id, msg)

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

    elif msg_type == "battery":
        if "level" in msg:
            publish_battery(client, topic_prefix, wiimote_id, int(msg["level"]))
