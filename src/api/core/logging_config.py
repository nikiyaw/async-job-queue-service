import logging
from logging import StreamHandler, Formatter
import sys

def setup_logging(level: str = "INFO"):
    """
    Configures global logging format, level, and handler.
    Call this at the start of your main entry point (API or worker).
    """
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Remove existing handlers (to avoid duplicate logs in some environments)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # StreamHandler to print to stdout
    handler = StreamHandler(sys.stdout)

    # Log format: timestamp | level | module | message
    formatter = Formatter(fmt="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
                          datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)

def get_logger(name: str):
    """
    Returns a logger with the given module name.
    """
    return logging.getLogger(name)