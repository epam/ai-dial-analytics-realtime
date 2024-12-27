from logging import Logger
from typing import List


def get_chat_completion_request_contents(
    logger: Logger, request: dict
) -> List[str]:
    return [
        content
        for message in request["messages"]
        for content in _get_chat_completion_message_contents(logger, message)
    ]


def get_chat_completion_response_contents(
    logger: Logger, response: dict
) -> List[str]:
    message = response["choices"][0]["message"]
    return _get_chat_completion_message_contents(logger, message)


def get_embeddings_request_contents(logger: Logger, request: dict) -> List[str]:
    inp = request.get("input")

    if isinstance(inp, str):
        return [inp]
    elif isinstance(inp, list):
        return [i for i in inp if isinstance(i, str)]
    else:
        logger.warning(f"Unexpected type of embeddings input: {type(inp)}")
        return []


def _get_chat_completion_message_contents(
    logger: Logger, message: dict
) -> List[str]:
    content = message.get("content")
    if content is None:
        return []
    elif isinstance(content, str):
        return [content]
    elif isinstance(content, list):
        ret: List[str] = []
        for content_part in content:
            if isinstance(content_part, dict):
                if content_part.get("type") == "text" and (
                    text := content_part.get("content")
                ):
                    ret.extend(text)
        return ret
    else:
        logger.warning(f"Unexpected message content type: {type(content)}")
        return []
