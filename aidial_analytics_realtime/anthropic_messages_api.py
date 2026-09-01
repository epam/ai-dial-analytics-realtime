from collections.abc import Iterator
from typing import Any

from aidial_analytics_realtime.utils.logging import app_logger as logger


def get_anthropic_messages_request_contents(request: dict | None) -> list[str]:
    if request is None:
        return []
    try:
        return list(_request_contents(request))
    except Exception as e:
        logger.error(f"Failed to get anthropic messages request contents: {e}")
        return []


def get_anthropic_messages_response_contents(
    response: dict | None,
) -> list[str]:
    if response is None:
        return []
    try:
        return list(_content_contents(response["content"]))
    except Exception as e:
        logger.error(f"Failed to get anthropic messages response contents: {e}")
        return []


def _request_contents(request: dict) -> Iterator[str]:
    # The system prompt is a top-level field rather than a message with the
    # "system" role, as in the chat completions.
    yield from _content_contents(request.get("system"))

    messages = request.get("messages")

    if isinstance(messages, list):
        for message in messages:
            if isinstance(message, dict):
                yield from _content_contents(message.get("content"))
    elif messages is not None:
        logger.warning(
            f"Unexpected type of anthropic messages: {type(messages)}"
        )


def _content_contents(content: Any) -> Iterator[str]:
    if content is None:
        return
    elif isinstance(content, str):
        yield from _non_empty_string(content)
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                yield from _block_contents(block)
    else:
        logger.warning(f"Unexpected anthropic content type: {type(content)}")


def _block_contents(block: dict) -> Iterator[str]:
    # The content block types carrying no user-visible text ("image",
    # "document", "tool_use", "redacted_thinking") are skipped. So are the
    # "thinking" blocks, so that the collected topic reflects the
    # conversation rather than the model thinking.
    match block.get("type"):
        case "text":
            yield from _non_empty_string(block.get("text") or "")
        # A tool result carries its text in a nested "content", which is
        # either a string or a list of content blocks. This mirrors the chat
        # completion path, which collects the content of the "tool" role
        # messages.
        case "tool_result":
            yield from _content_contents(block.get("content"))


def _non_empty_string(value: str) -> Iterator[str]:
    if non_empty := value.strip():
        yield non_empty
