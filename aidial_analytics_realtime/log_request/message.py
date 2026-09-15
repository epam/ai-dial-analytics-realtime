from aidial_analytics_realtime.utils.json import parse_json


def get_assembled_response(message: dict) -> dict | None:
    assembled_response = parse_json(
        message.get("assembled_response"), "assembled_response"
    )
    if assembled_response is None:
        return None

    # NOTE: this transformation becomes redundant in ai-dial-core>=0.22.1
    # due to the fix https://github.com/epam/ai-dial-core/pull/648
    for choice in assembled_response.get("choices") or []:
        if "delta" in choice:
            choice["message"] = choice["delta"]
            del choice["delta"]

    return assembled_response
