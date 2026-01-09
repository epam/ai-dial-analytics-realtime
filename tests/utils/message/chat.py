from tests.utils.constants import (
    DEFAULT_CHAT_ID,
    DEFAULT_EXECUTION_PATH_LIST,
    DEFAULT_PROJECT_ID,
    DEFAULT_RESPONSE_ID,
    DEFAULT_RESPONSE_TIME,
    DEFAULT_UPSTREAM_URI,
    DEFAULT_USER_ID,
    DEFAULT_USER_TITLE,
)
from tests.utils.message.base import (
    create_message,
    default_token_usage,
    default_trace,
)


def create_chat_request(content: str = "default-user-message"):
    return {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": content}],
    }


def create_chat_assembled_response(
    *,
    id: str = DEFAULT_RESPONSE_ID,
    content: str = "default-assistant-message",
):
    delta = {"role": "assistant", "content": content}
    return {
        "id": id,
        "object": "chat.completion.chunk",
        "created": 1692214960,
        "model": "gpt-4",
        "choices": [{"index": 0, "delta": delta, "finish_reason": "stop"}],
        "usage": {
            "completion_tokens": 189,
            "prompt_tokens": 22,
            "total_tokens": 211,
            "prompt_tokens_details": {"cached_tokens": 10},
        },
    }


def create_chat_message(
    *,
    chat_id: str = DEFAULT_CHAT_ID,
    project_id: str = DEFAULT_PROJECT_ID,
    user_id: str = DEFAULT_USER_ID,
    user_title: str = DEFAULT_USER_TITLE,
    deployment: str = "gpt-4",
    request_uri: str = "/openai/deployments/test-deployment-id/chat/completions",
    token_usage: dict | None = default_token_usage(),
    parent_deployment: str | None = "assistant",
    trace: dict | None = default_trace(),
    execution_path: list | None = DEFAULT_EXECUTION_PATH_LIST,
    request_time: str = DEFAULT_RESPONSE_TIME,
    request_body: str | dict | None = create_chat_request(),
    response_assembled: str | dict | None = create_chat_assembled_response(),
    # response.body is never inspected by the analytics for chat completions requests,
    # therefore, no need to make it realistic.
    response_body: str | dict | None = "whatever",
    response_upstream_uri: str | None = DEFAULT_UPSTREAM_URI,
) -> dict:
    return create_message(**locals())
