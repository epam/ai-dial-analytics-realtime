from tests.utils.constants import (
    DEFAULT_CHAT_ID,
    DEFAULT_PROJECT_ID,
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


def _default_embedding_request_body() -> dict:
    return {"input": ["default-embedding-input"]}


def _default_embedding_response_body() -> dict:
    return {
        "object": "list",
        "model": "text-embedding-3-small",
        "data": [{"index": 0, "object": "embedding", "embedding": [0.1, 0.2]}],
        "usage": {"prompt_tokens": 43, "total_tokens": 43},
    }


def create_embedding_message(
    *,
    chat_id: str = DEFAULT_CHAT_ID,
    project_id: str = DEFAULT_PROJECT_ID,
    user_id: str = DEFAULT_USER_ID,
    user_title: str = DEFAULT_USER_TITLE,
    deployment: str = "text-embedding-3-small",
    request_uri: str = "/openai/deployments/text-embedding-3-small/embeddings?api-version=2023-03-15-preview",
    token_usage: dict | None = default_token_usage(),
    parent_deployment: str | None = "assistant",
    trace: dict | None = default_trace(),
    execution_path: list | None = ["app1", "app2"],
    request_time: str = DEFAULT_RESPONSE_TIME,
    request_body: str | dict | None = _default_embedding_request_body(),
    response_assembled: str | dict | None = None,
    response_body: str | dict | None = _default_embedding_response_body(),
    response_upstream_uri: str | None = DEFAULT_UPSTREAM_URI,
) -> dict:
    return create_message(**locals())
