import serial

from ..utils.config import Settings
from ..utils.logging import get_logger


LOGGER = get_logger(__name__)


def open_serial(settings: Settings) -> serial.Serial:
    LOGGER.info("Opening serial port %s at %s baud", settings.serial_port, settings.serial_baud)
    return serial.Serial(settings.serial_port, settings.serial_baud, timeout=1)
