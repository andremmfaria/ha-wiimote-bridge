import json
import os
from dataclasses import dataclass

from dynaconf import Dynaconf


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
    mqtt_transport: str = "tcp"
    mqtt_ssl: bool = False
    mqtt_ssl_insecure: bool = False
    log_level: str = "info"


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
                baud=int(radio["baud"]),
                controller_id=int(radio["controller_id"]),
            )
        )

    return tuple(radios)


def _parse_mqtt_transport(value: object) -> str:
    transport = str(value).strip().lower()
    if transport in {"tcp", "websockets"}:
        return transport
    return "tcp"


def _default_mqtt_port(transport: str, tls_enabled: bool) -> int:
    if transport == "websockets":
        return 8884 if tls_enabled else 1884
    return 8883 if tls_enabled else 1883


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

    mqtt_port = configured_port if configured_port > 0 else _default_mqtt_port(mqtt_transport, mqtt_ssl)

    return Settings(
        radios=radios,
        discover_enabled=_as_bool(settings.get("DISCOVER_ENABLED", "true"), default=True),
        mqtt_host=settings.get("MQTT_HOST", "core-mosquitto"),
        mqtt_port=mqtt_port,
        mqtt_username=settings.get("MQTT_USERNAME", ""),
        mqtt_password=settings.get("MQTT_PASSWORD", ""),
        mqtt_transport=mqtt_transport,
        mqtt_ssl=mqtt_ssl,
        mqtt_ssl_insecure=_as_bool(settings.get("MQTT_SSL_INSECURE", "false"), default=False),
        topic_prefix=settings.get("TOPIC_PREFIX", "wiimote"),
        log_level=str(settings.get("LOG_LEVEL", "info")).lower(),
    )
