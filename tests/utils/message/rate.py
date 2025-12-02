from tests.utils.constants import (
    DEFAULT_CHAT_ID,
    DEFAULT_PROJECT_ID,
    DEFAULT_RESPONSE_ID,
    DEFAULT_RESPONSE_TIME,
    DEFAULT_USER_ID,
    DEFAULT_USER_TITLE,
)
from tests.utils.message.base import create_message, default_trace


def _default_rate_request_body():
    return {"responseId": DEFAULT_RESPONSE_ID, "rate": True}


def create_rate_message(
    *,
    chat_id: str = DEFAULT_CHAT_ID,
    project_id: str = DEFAULT_PROJECT_ID,
    user_id: str = DEFAULT_USER_ID,
    user_title: str = DEFAULT_USER_TITLE,
    deployment: str = "gpt-4",
    request_uri: str = "/v1/gpt-4/rate",
    token_usage: dict | None = None,
    parent_deployment: str | None = "assistant",
    trace: dict | None = default_trace(),
    execution_path: list | None = ["app1", "app2"],
    request_time: str = DEFAULT_RESPONSE_TIME,
    request_body: str | dict | None = _default_rate_request_body(),
    response_assembled: str | dict | None = None,
    response_body: str | dict | None = "",
    response_upstream_uri: str | None = None,
) -> dict:
    return create_message(**locals())
