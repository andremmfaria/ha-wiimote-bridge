import socket
import ssl
from typing import Any, cast

import paho.mqtt.client as mqtt

from wiimote_bridge.utils.config import Settings


def _is_auth_failure_message(message: str) -> bool:
    normalized = message.strip().lower()
    return (
        "bad user name or password" in normalized
        or "not authorized" in normalized
        or "not authorised" in normalized
    )


def _describe_connect_reason(reason_code: Any) -> str:
    try:
        message = mqtt.connack_string(reason_code)
    except Exception:
        message = str(reason_code).strip() or mqtt.error_string(mqtt.MQTT_ERR_UNKNOWN)

    return message


def _describe_disconnect_reason(reason_code: Any) -> str:
    try:
        if isinstance(reason_code, int):
            disconnect_code = cast(mqtt.MQTTErrorCode, reason_code)
            return str(mqtt.convert_disconnect_error_code_to_reason_code(disconnect_code))
        return str(reason_code).strip() or mqtt.error_string(mqtt.MQTT_ERR_UNKNOWN)
    except Exception:
        return str(reason_code).strip() or mqtt.error_string(mqtt.MQTT_ERR_UNKNOWN)


def _mqtt_credentials_hint(missing_username: bool) -> str:
    if missing_username:
        return "The broker likely requires authentication; fill in mqtt.username and mqtt.password in the add-on options"
    return "Check mqtt.username and mqtt.password in the add-on options"


def _mqtt_tls_hint() -> str:
    return "Check mqtt.ssl, mqtt.ssl_insecure, and the broker certificate configuration"


def _mqtt_network_hint() -> str:
    return "Check mqtt.host, mqtt.port, and that the broker is running and reachable from the add-on"


def _mqtt_hostname_hint() -> str:
    return (
        "Check mqtt.host and ensure the broker hostname is resolvable from the add-on"
    )


def _format_mqtt_failure(message: str, settings: Settings) -> str:
    normalized = message.strip()
    lowered = normalized.lower()

    hint: str | None = None
    if _is_auth_failure_message(normalized):
        hint = _mqtt_credentials_hint(not bool(settings.mqtt_username))
    elif any(
        token in lowered
        for token in ("certificate", "tls", "ssl", "wrong version number")
    ):
        hint = _mqtt_tls_hint()
    elif any(
        token in lowered
        for token in (
            "name resolution",
            "resolve mqtt host",
            "nodename nor servname",
            "name or service not known",
        )
    ):
        hint = _mqtt_hostname_hint()
    elif any(
        token in lowered
        for token in (
            "connection refused",
            "network error",
            "timed out",
            "timeout",
            "unreachable",
        )
    ):
        hint = _mqtt_network_hint()

    if hint is None or hint.lower() in lowered:
        return normalized

    suffix = "" if normalized.endswith((".", "!", "?")) else "."
    return f"{normalized}{suffix} {hint}"


def _describe_connect_exception(exc: Exception, settings: Settings) -> str:
    if isinstance(exc, socket.gaierror):
        return f"Name resolution failed for MQTT host {settings.mqtt_host}: {exc}"

    if isinstance(exc, ConnectionRefusedError):
        return f"TCP connection refused by MQTT broker at {settings.mqtt_host}:{settings.mqtt_port}: {exc}"

    if isinstance(exc, (TimeoutError, socket.timeout)):
        return f"Connection to MQTT broker at {settings.mqtt_host}:{settings.mqtt_port} timed out: {exc}"

    if isinstance(exc, ssl.SSLError):
        return f"TLS handshake failed while connecting to MQTT broker at {settings.mqtt_host}:{settings.mqtt_port}: {exc}"

    if isinstance(exc, OSError):
        return f"Network error while connecting to MQTT broker at {settings.mqtt_host}:{settings.mqtt_port}: {exc}"

    return str(exc).strip() or mqtt.error_string(mqtt.MQTT_ERR_UNKNOWN)
