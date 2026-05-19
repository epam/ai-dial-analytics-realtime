import os

from aidial_analytics_realtime.utils.logging import app_logger as logger


def check_deprecations():
    if os.getenv("MODEL_RATES") is not None:
        logger.warning(
            "The MODEL_RATES environment variable has become redundant since "
            "DIAL Core 0.7.0. It's ignored by the analytics service and could"
            " be safely removed."
        )
