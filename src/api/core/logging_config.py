import logging
from logging import StreamHandler
import sys
import os

try:
    from pythonjsonlogger import jsonlogger
except ImportError:
    jsonlogger = None

def setup_logging(level: str = "INFO", json_logs: bool = False):
    """
    Configures global logging format, level, and handler.
    If json_logs=True, uses JSON formatter (requires python-json-logger).
    """

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Remove existing handlers (avoid duplicate logs if setup_logging is called multiple times)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # StreamHandler to print to stdout
    handler = StreamHandler(sys.stdout)

    if json_logs and jsonlogger:
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def get_logger(name: str):
    """
    Returns a logger with the given module name.
    """
    return logging.getLogger(name)