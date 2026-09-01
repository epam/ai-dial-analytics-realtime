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


def create_responses_request(
    *,
    model: str = DEFAULT_MODEL,
    input: str | list = "default-user-message",
):
    return {"model": model, "input": input}


def create_responses_assembled_response(
    *,
    id: str = DEFAULT_RESPONSE_ID,
    content: str = "default-assistant-message",
):
    return {
        "id": id,
        "object": "response",
        "created_at": 1785851850,
        "model": "whatever-model-id",
        "status": "completed",
        "output": [
            {
                "id": "rs_whatever",
                "type": "reasoning",
                "summary": [{"text": "thinking", "type": "summary_text"}],
                "content": [],
            },
            {
                "id": "msg_whatever",
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [{"text": content, "type": "output_text"}],
            },
        ],
        "usage": {
            "input_tokens": 22,
            "input_tokens_details": {
                "cached_tokens": 10,
                "cache_write_tokens": 5,
            },
            "output_tokens": 189,
            "output_tokens_details": {"reasoning_tokens": 100},
            "total_tokens": 211,
        },
    }


def create_responses_message(
    *,
    chat_id: str = DEFAULT_CHAT_ID,
    project_id: str = DEFAULT_PROJECT_ID,
    user_id: str = DEFAULT_USER_ID,
    user_title: str = DEFAULT_USER_TITLE,
    deployment: str = DEFAULT_DEPLOYMENT,
    request_uri: str = "/openai/v1/responses",
    token_usage: dict | None = default_token_usage(),
    parent_deployment: str | None = DEFAULT_PARENT_DEPLOYMENT,
    trace: dict | None = default_trace(),
    execution_path: list | None = DEFAULT_EXECUTION_PATH_LIST,
    request_http_method: str = DEFAULT_REQUEST_METHOD,
    request_time: str = DEFAULT_RESPONSE_TIME,
    request_body: str | dict | None = create_responses_request(),
    response_assembled: str
    | dict
    | None = create_responses_assembled_response(),
    # response.body is never inspected by the analytics for responses requests,
    # therefore, no need to make it realistic.
    response_body: str | dict | None = "whatever",
    response_upstream_uri: str | None = DEFAULT_UPSTREAM_URI,
    response_status: str = DEFAULT_RESPONSE_STATUS,
) -> dict:
    return create_message(**locals())
