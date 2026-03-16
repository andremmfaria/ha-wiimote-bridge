import logging

from wiimote_bridge.utils.logging import LOG_LEVELS, configure_logging, get_logger


def test_configure_logging_returns_normalized_level():
    assert configure_logging("info") == "info"
    assert configure_logging("DEBUG") == "debug"
    assert configure_logging("WARNING") == "warning"
    assert configure_logging("ERROR") == "error"


def test_configure_logging_unknown_level_returns_info():
    assert configure_logging("verbose") == "info"
    assert configure_logging("") == "info"


def test_configure_logging_sets_level_on_existing_handlers():
    root = logging.getLogger()
    handler = logging.StreamHandler()
    # Ensure there is at least one handler so the else-branch is exercised.
    original_handlers = root.handlers[:]
    root.handlers = [handler]

    try:
        configure_logging("warning")

        assert root.level == logging.WARNING
        assert handler.level == logging.WARNING
    finally:
        root.handlers = original_handlers


def test_configure_logging_with_basicconfig_when_no_handlers():
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    root.handlers = []

    try:
        result = configure_logging("debug")
        assert result == "debug"
        # basicConfig should have added at least one handler.
        assert len(root.handlers) >= 1
        assert root.level == logging.DEBUG
    finally:
        # Restore original handlers.
        root.handlers = original_handlers


def test_log_levels_contains_all_expected_keys():
    assert set(LOG_LEVELS.keys()) == {"debug", "info", "warning", "error"}
    assert LOG_LEVELS["debug"] == logging.DEBUG
    assert LOG_LEVELS["info"] == logging.INFO
    assert LOG_LEVELS["warning"] == logging.WARNING
    assert LOG_LEVELS["error"] == logging.ERROR


def test_get_logger_returns_logger_with_correct_name():
    logger = get_logger("my.module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "my.module"


def test_get_logger_default_name():
    logger = get_logger()
    assert logger.name == "wiimote_bridge"
