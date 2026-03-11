from dataclasses import dataclass

from dynaconf import Dynaconf


@dataclass(frozen=True)
class Settings:
    serial_port: str
    serial_baud: int
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str
    mqtt_password: str
    topic_prefix: str


def load_settings() -> Settings:
    settings = Dynaconf(environments=False, envvar_prefix=False)

    return Settings(
        serial_port=settings.get("SERIAL_PORT", "/dev/ttyUSB0"),
        serial_baud=int(settings.get("SERIAL_BAUD", 115200)),
        mqtt_host=settings.get("MQTT_HOST", "core-mosquitto"),
        mqtt_port=int(settings.get("MQTT_PORT", 1883)),
        mqtt_username=settings.get("MQTT_USERNAME", ""),
        mqtt_password=settings.get("MQTT_PASSWORD", ""),
        topic_prefix=settings.get("TOPIC_PREFIX", "wiimote"),
    )
