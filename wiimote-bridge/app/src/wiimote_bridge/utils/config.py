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
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str
    mqtt_password: str
    topic_prefix: str
    log_level: str = "info"


_DEFAULT_RADIOS = '[{"port":"/dev/ttyUSB0","baud":115200,"controller_id":1}]'


def load_settings() -> Settings:
    settings = Dynaconf(environments=False, envvar_prefix=False)

    radios_raw = os.environ.get("RADIOS", _DEFAULT_RADIOS)
    radios_data = json.loads(radios_raw)
    radios = tuple(
        RadioConfig(
            port=str(r["port"]),
            baud=int(r["baud"]),
            controller_id=int(r["controller_id"]),
        )
        for r in radios_data
    )

    return Settings(
        radios=radios,
        mqtt_host=settings.get("MQTT_HOST", "core-mosquitto"),
        mqtt_port=int(settings.get("MQTT_PORT", 1883)),
        mqtt_username=settings.get("MQTT_USERNAME", ""),
        mqtt_password=settings.get("MQTT_PASSWORD", ""),
        topic_prefix=settings.get("TOPIC_PREFIX", "wiimote"),
        log_level=str(settings.get("LOG_LEVEL", "info")).lower(),
    )
