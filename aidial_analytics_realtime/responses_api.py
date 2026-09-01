from collections.abc import Iterator
from typing import Any

from aidial_analytics_realtime.utils.logging import app_logger as logger

# The content part types carrying user-visible text. The other part types
# ("input_image", "input_file", "refusal") carry no text usable for the
# language and the topic detection. The reasoning summaries ("summary_text")
# are deliberately left out, so that the collected topic reflects the
# conversation rather than the model thinking.
_TEXT_PART_TYPES = frozenset({"input_text", "output_text"})


def get_responses_request_contents(request: dict | None) -> list[str]:
    if request is None:
        return []
    try:
        return list(_request_contents(request))
    except Exception as e:
        logger.error(f"Failed to get responses request contents: {e}")
        return []


def get_responses_response_contents(response: dict | None) -> list[str]:
    if response is None:
        return []
    try:
        return list(_response_contents(response))
    except Exception as e:
        logger.error(f"Failed to get responses response contents: {e}")
        return []


def _request_contents(request: dict) -> Iterator[str]:
    inp = request.get("input")

    # A bare string input is a shorthand for a single user message.
    if isinstance(inp, str):
        yield from _non_empty_string(inp)
    elif isinstance(inp, list):
        for item in inp:
            if isinstance(item, dict):
                yield from _item_contents(item)
    elif inp is not None:
        logger.warning(f"Unexpected type of responses input: {type(inp)}")


def _response_contents(response: dict) -> Iterator[str]:
    for item in response["output"]:
        if isinstance(item, dict):
            yield from _item_contents(item)


def _item_contents(item: dict) -> Iterator[str]:
    # A function call result carries its text in "output", not in "content".
    # This mirrors the chat completion path, which collects the content of
    # the "tool" role messages.
    content: Any = (
        item.get("output")
        if item.get("type") == "function_call_output"
        else item.get("content")
    )

    if content is None:
        return
    elif isinstance(content, str):
        yield from _non_empty_string(content)
    elif isinstance(content, list):
        for content_part in content:
            if (
                isinstance(content_part, dict)
                and content_part.get("type") in _TEXT_PART_TYPES
                and (text := content_part.get("text"))
            ):
                yield from _non_empty_string(text)
    else:
        logger.warning(f"Unexpected responses content type: {type(content)}")


def _non_empty_string(value: str) -> Iterator[str]:
    if non_empty := value.strip():
        yield non_empty
