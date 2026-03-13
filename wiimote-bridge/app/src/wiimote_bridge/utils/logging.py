import logging


LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def configure_logging(level_name: str = "info") -> str:
    normalized_level = level_name.lower()
    level = LOG_LEVELS.get(normalized_level, logging.INFO)
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")
    else:
        root_logger.setLevel(level)
        for handler in root_logger.handlers:
            handler.setLevel(level)

    return normalized_level if normalized_level in LOG_LEVELS else "info"


def get_logger(name: str = "wiimote_bridge") -> logging.Logger:
    return logging.getLogger(name)
