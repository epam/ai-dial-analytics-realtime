import logging
import os
from contextvars import ContextVar

from aidial_sdk import LogConfig, configure_root_logger

app_logger = logging.getLogger("app")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def configure_loggers():
    # Delegate to the SDK to install a uniformly formatted root logger
    # handler and to route uvicorn logs through it, preserving this
    # repo's original text log format.
    configure_root_logger(
        LogConfig(
            text_format="%(levelprefix)s | %(asctime)s | %(process)d | %(name)s | %(message)s"  # noqa: E501
        )
    )

    # Setting log levels for the analytics application
    app_logger.setLevel(LOG_LEVEL)

    for handler in logging.getLogger().handlers:
        handler.addFilter(_PrefixFilter())


_logger_prefix: ContextVar[str] = ContextVar("_logger_prefix", default="")


def add_logger_prefix(prefix: str) -> None:
    _logger_prefix.set(_logger_prefix.get() + prefix)


class _PrefixFilter(logging.Filter):
    def __init__(self, name: str = "") -> None:
        super().__init__(name)

    def filter(self, record):
        if prefix := _logger_prefix.get():
            record.msg = f"{prefix} {record.msg}"
        return True
