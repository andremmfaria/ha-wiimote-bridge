import logging


def get_logger(name: str = "wiimote_bridge") -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    return logging.getLogger(name)
