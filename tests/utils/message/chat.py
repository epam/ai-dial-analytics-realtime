from tests.utils.constants import (
    DEFAULT_CHAT_ID,
    DEFAULT_DEPLOYMENT,
    DEFAULT_EXECUTION_PATH_LIST,
    DEFAULT_MODEL,
    DEFAULT_PARENT_DEPLOYMENT,
    DEFAULT_PROJECT_ID,
    DEFAULT_REQUEST_METHOD,
    DEFAULT_RESPONSE_ID,
    DEFAULT_RESPONSE_STATUS,
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


def create_chat_request(
    *,
    model: str = DEFAULT_MODEL,
    messages: list[dict] = [
        {"role": "user", "content": "default-user-message"}
    ],
):
    return {"model": model, "messages": messages}


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
        "model": "whatever-model-id",
        "choices": [{"index": 0, "delta": delta, "finish_reason": "stop"}],
        "usage": {
            "completion_tokens": 189,
            "prompt_tokens": 22,
            "total_tokens": 211,
            "prompt_tokens_details": {
                "cached_tokens": 10,
                "cache_write_tokens": 5,
            },
            "completion_tokens_details": {"reasoning_tokens": 100},
        },
    }


def create_chat_message(
    *,
    chat_id: str = DEFAULT_CHAT_ID,
    project_id: str = DEFAULT_PROJECT_ID,
    user_id: str = DEFAULT_USER_ID,
    user_title: str = DEFAULT_USER_TITLE,
    deployment: str = DEFAULT_DEPLOYMENT,
    request_uri: str = "/openai/deployments/whatever-deployment-id/chat/completions",
    token_usage: dict | None = default_token_usage(),
    parent_deployment: str | None = DEFAULT_PARENT_DEPLOYMENT,
    trace: dict | None = default_trace(),
    execution_path: list | None = DEFAULT_EXECUTION_PATH_LIST,
    request_http_method: str = DEFAULT_REQUEST_METHOD,
    request_time: str = DEFAULT_RESPONSE_TIME,
    request_body: str | dict | None = create_chat_request(),
    response_assembled: str | dict | None = create_chat_assembled_response(),
    # response.body is never inspected by the analytics for chat completions requests,
    # therefore, no need to make it realistic.
    response_body: str | dict | None = "whatever",
    response_upstream_uri: str | None = DEFAULT_UPSTREAM_URI,
    response_status: str = DEFAULT_RESPONSE_STATUS,
) -> dict:
    return create_message(**locals())
