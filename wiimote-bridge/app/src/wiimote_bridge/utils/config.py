import json
import os
from dataclasses import dataclass

from dynaconf import Dynaconf

from wiimote_bridge.utils.types import MqttTransport


@dataclass(frozen=True)
class RadioConfig:
    port: str
    baud: int
    controller_id: int


@dataclass(frozen=True)
class Settings:
    radios: tuple[RadioConfig, ...]
    discover_enabled: bool
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str
    mqtt_password: str
    topic_prefix: str
    mqtt_transport: MqttTransport = "tcp"
    mqtt_ssl: bool = False
    mqtt_ssl_insecure: bool = False
    log_level: str = "info"
    health_port: int = 0


_DEFAULT_RADIOS = '[{"port":"/dev/ttyUSB0","baud":115200,"controller_id":1}]'


def _as_bool(value: object, default: bool = True) -> bool:
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _parse_radios(raw_value: object) -> tuple[RadioConfig, ...]:
    radios_data: object = raw_value

    # Most environments pass a JSON string, but Home Assistant/bashio
    # can occasionally provide a single object or an extra-quoted JSON string.
    while isinstance(radios_data, str):
        radios_data = json.loads(radios_data)

    if isinstance(radios_data, dict):
        radios_list: list[dict[str, object]] = [radios_data]
    elif isinstance(radios_data, list):
        radios_list = radios_data
    else:
        raise ValueError("RADIOS must be a JSON list or object")

    radios = []
    for radio in radios_list:
        if not isinstance(radio, dict):
            raise ValueError("Each radio entry must be an object")
        radios.append(
            RadioConfig(
                port=str(radio["port"]),
                baud=_parse_int(radio["baud"], "baud"),
                controller_id=_parse_int(radio["controller_id"], "controller_id"),
            )
        )

    return tuple(radios)


def _parse_int(value: object, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        raise ValueError(f"{field_name} must be an integer")

    if isinstance(value, str):
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an integer") from exc

    raise ValueError(f"{field_name} must be an integer")


def _parse_mqtt_transport(value: object) -> MqttTransport:
    transport = str(value).strip().lower()
    if transport == "websockets":
        return "websockets"
    return "tcp"


def _default_mqtt_port(transport: MqttTransport, tls_enabled: bool) -> int:
    if transport == "websockets":
        return 8884 if tls_enabled else 1884
    return 8883 if tls_enabled else 1883


def _parse_health_port(value: object) -> int:
    try:
        port = _parse_int(value, "health_port")
    except ValueError:
        return 0
    return port if port > 0 else 0


def load_settings() -> Settings:
    settings = Dynaconf(environments=False, envvar_prefix=False)

    radios_raw = os.environ.get("RADIOS", _DEFAULT_RADIOS)
    radios = _parse_radios(radios_raw)
    mqtt_transport = _parse_mqtt_transport(settings.get("MQTT_TRANSPORT", "tcp"))
    mqtt_ssl = _as_bool(settings.get("MQTT_SSL", "false"), default=False)

    configured_port_raw = settings.get("MQTT_PORT", "0")
    try:
        configured_port = int(configured_port_raw)
    except (TypeError, ValueError):
        configured_port = 0

    mqtt_port = (
        configured_port
        if configured_port > 0
        else _default_mqtt_port(mqtt_transport, mqtt_ssl)
    )

    return Settings(
        radios=radios,
        discover_enabled=_as_bool(
            settings.get("DISCOVER_ENABLED", "true"), default=True
        ),
        mqtt_host=settings.get("MQTT_HOST", "core-mosquitto"),
        mqtt_port=mqtt_port,
        mqtt_username=settings.get("MQTT_USERNAME", ""),
        mqtt_password=settings.get("MQTT_PASSWORD", ""),
        mqtt_transport=mqtt_transport,
        mqtt_ssl=mqtt_ssl,
        mqtt_ssl_insecure=_as_bool(
            settings.get("MQTT_SSL_INSECURE", "false"), default=False
        ),
        topic_prefix=settings.get("TOPIC_PREFIX", "wiimote"),
        log_level=str(settings.get("LOG_LEVEL", "info")).lower(),
        health_port=_parse_health_port(settings.get("HEALTH_PORT", "0")),
    )
