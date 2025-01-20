import json


def get_assembled_response(message: dict) -> dict | None:
    if (assembled_response_str := message.get("assembled_response")) is None:
        return None

    assembled_response = json.loads(assembled_response_str)

    # NOTE: this becomes redundant when https://github.com/epam/ai-dial-core/pull/648
    # is merged and deployed to production
    for choice in assembled_response.get("choices") or []:
        if "delta" in choice:
            choice["message"] = choice["delta"]
            del choice["delta"]

    return assembled_response
