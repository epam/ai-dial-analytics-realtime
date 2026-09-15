import json

from aidial_analytics_realtime.utils.logging import app_logger as logger


def parse_json(value: str | None, *, json_path: str, api: str) -> dict | None:
    if value is None:
        return None

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        logger.error(
            f"{json_path} in the {api} API log message isn't valid JSON"
        )
        return None
