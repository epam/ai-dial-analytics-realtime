import logging
import os
import sys
from typing import Callable

from typing_extensions import override
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

    root_has_stderr_handler = any(
        isinstance(handler, logging.StreamHandler)
        and handler.stream == sys.stderr
        for handler in root.handlers
    )

    # Do not override the existing stderr handlers
    # if they are already configured
    if not root_has_stderr_handler:
        formatter = DefaultFormatter(
            fmt="%(levelprefix)s | %(asctime)s | %(process)d | %(name)s | %(message)s",
            use_colors=True,
        )

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        root.addHandler(handler)


class _MessageHookLogger(logging.LoggerAdapter):
    _on_message: Callable[[str], str]

    def __init__(
        self, logger: logging.Logger, on_message: Callable[[str], str]
    ):
        super().__init__(logger)
        self._on_message = on_message

    @override
    def process(self, msg, kwargs):
        return self._on_message(msg), kwargs


def with_prefix(logger: logging.Logger, prefix: str) -> logging.Logger:
    def on_message(msg: str) -> str:
        if msg and msg[0].isalnum():
            return f"{prefix} {msg}"
        return f"{prefix}{msg}"

    return _MessageHookLogger(logger, on_message)  # type: ignore
