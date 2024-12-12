import logging
import sys

from uvicorn.logging import DefaultFormatter

logger = logging.getLogger("app")


def configure_loggers():
    # Delegate uvicorn logs to the root logger
    # to achieve uniform log formatting
    for name, log in logging.getLogger().manager.loggerDict.items():
        if isinstance(log, logging.Logger) and name.startswith("uvicorn"):
            log.handlers = []
            log.propagate = True

    # Setting up log levels
    logger.setLevel(logging.DEBUG)

    # Configuring the root logger
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    root_has_stderr_handler = any(
        isinstance(handler, logging.StreamHandler)
        and handler.stream == sys.stderr
        for handler in root.handlers
    )

    # Do not override the existing stderr handlers
    # if they are already configured
    if not root_has_stderr_handler:
        formatter = DefaultFormatter(
            fmt="%(asctime)s [%(levelname)s] - %(message)s"
        )

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        root.addHandler(handler)
