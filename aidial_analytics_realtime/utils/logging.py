import logging
import os
import sys
from contextvars import ContextVar

from uvicorn.logging import DefaultFormatter

app_logger = logging.getLogger("app")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def configure_loggers():
    # Delegate uvicorn logs to the root logger
    # to achieve uniform log formatting
    for name, log in logging.getLogger().manager.loggerDict.items():
        if isinstance(log, logging.Logger) and name.startswith("uvicorn"):
            log.handlers = []
            log.propagate = True

    # Setting log levels for the analytics application
    app_logger.setLevel(LOG_LEVEL)

    # Configuring the root logger
    root = logging.getLogger()

    stderr_handler = next(
        (
            handler
            for handler in root.handlers
            if isinstance(handler, logging.StreamHandler)
            and handler.stream == sys.stderr
        ),
        None,
    )

    # Do not override the existing stderr handlers
    # if they are already configured
    if stderr_handler is None:
        formatter = DefaultFormatter(
            fmt="%(levelprefix)s | %(asctime)s | %(process)d | %(name)s | %(message)s",  # noqa: E501
            use_colors=True,
        )

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        handler.addFilter(_PrefixFilter())
        root.addHandler(handler)
    else:
        stderr_handler.addFilter(_PrefixFilter())


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
