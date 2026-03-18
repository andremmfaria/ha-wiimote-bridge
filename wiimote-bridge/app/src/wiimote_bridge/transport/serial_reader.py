import serial

from wiimote_bridge.utils.logging import get_logger

LOGGER = get_logger(__name__)


def open_serial(port: str, baud: int) -> serial.Serial:
    LOGGER.info("Opening serial port %s at %s baud", port, baud)
    return serial.Serial(port, baud, timeout=1)
