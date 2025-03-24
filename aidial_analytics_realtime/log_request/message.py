import json

from aidial_analytics_realtime.utils.logging import app_logger as logger


def get_assembled_response(message: dict) -> dict | None:
    if (assembled_response_str := message.get("assembled_response")) is None:
        return None

    try:
        assembled_response = json.loads(assembled_response_str)
    except json.JSONDecodeError:
        logger.error("The assembled response isn't a valid JSON")
        return None

    # NOTE: this transformation becomes redundant in ai-dial-core>=0.22.1
    # due to the fix https://github.com/epam/ai-dial-core/pull/648
    for choice in assembled_response.get("choices") or []:
        if "delta" in choice:
            choice["message"] = choice["delta"]
            del choice["delta"]

    return assembled_response
