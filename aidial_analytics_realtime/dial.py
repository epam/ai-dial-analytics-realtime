from typing import Iterator, List

from aidial_analytics_realtime.utils.logging import app_logger as logger


def get_chat_completion_request_contents(request: dict | None) -> List[str]:
    if request is None:
        return []
    try:
        return list(_chat_completion_request_contents(request))
    except Exception as e:
        logger.error(f"Failed to get chat completion request contents: {e}")
        return []


def get_chat_completion_response_contents(response: dict | None) -> List[str]:
    if response is None:
        return []
    try:
        return list(_chat_completion_response_contents(response))
    except Exception as e:
        logger.error(f"Failed to get chat completion response contents: {e}")
        return []


def get_embeddings_request_contents(request: dict) -> List[str]:
    try:
        return list(_embeddings_request_contents(request))
    except Exception as e:
        logger.error(f"Failed to get embeddings request contents: {e}")
        return []


def _chat_completion_request_contents(request: dict) -> Iterator[str]:
    for message in request["messages"]:
        yield from _chat_completion_message_contents(message)


def _chat_completion_response_contents(response: dict) -> Iterator[str]:
    message = response["choices"][0]["message"]
    yield from _chat_completion_message_contents(message)


def _embeddings_request_contents(request: dict) -> Iterator[str]:
    inp = request.get("input")

    if isinstance(inp, str):
        yield from _non_empty_string(inp)
    elif isinstance(inp, list):
        for i in inp:
            if isinstance(i, str):
                yield from _non_empty_string(i)
    else:
        logger.warning(f"Unexpected type of embeddings input: {type(inp)}")


def _chat_completion_message_contents(message: dict) -> Iterator[str]:
    content = message.get("content")
    if content is None:
        return
    elif isinstance(content, str):
        yield from _non_empty_string(content)
    elif isinstance(content, list):
        for content_part in content:
            if isinstance(content_part, dict):
                if content_part.get("type") == "text" and (
                    text := content_part.get("text")
                ):
                    yield from _non_empty_string(text)
    else:
        logger.warning(f"Unexpected message content type: {type(content)}")


def _non_empty_string(value: str) -> Iterator[str]:
    if non_empty := value.strip():
        yield non_empty
