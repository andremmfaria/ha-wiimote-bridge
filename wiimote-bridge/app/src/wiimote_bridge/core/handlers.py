import paho.mqtt.client as mqtt

from wiimote_bridge.transport.mqtt.publish import (battery, button, connected,
                                                   event_message, heartbeat)
from wiimote_bridge.utils.types import MessagePayload


def handle_message(
    client: mqtt.Client, topic_prefix: str, wiimote_id: int, msg: MessagePayload
) -> None:
    msg_type = msg.get("type")

    event_message(client, topic_prefix, wiimote_id, msg)

    if msg_type == "btn":
        button_name = msg.get("btn")
        down = bool(msg.get("down", False))
        if isinstance(button_name, str) and button_name:
            button(client, topic_prefix, wiimote_id, button_name, down)

    elif msg_type == "status":
        if "connected" in msg:
            connected(client, topic_prefix, wiimote_id, bool(msg["connected"]))

    elif msg_type == "heartbeat":
        heartbeat(client, topic_prefix, wiimote_id, msg)

    elif msg_type == "battery":
        if "level" in msg:
            battery(client, topic_prefix, wiimote_id, int(msg["level"]))
