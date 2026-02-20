from tests.utils.constants import (
    DEFAULT_CHAT_ID,
    DEFAULT_DEPLOYMENT,
    DEFAULT_EXECUTION_PATH_LIST,
    DEFAULT_PARENT_DEPLOYMENT,
    DEFAULT_PROJECT_ID,
    DEFAULT_RESPONSE_ID,
    DEFAULT_RESPONSE_STATUS,
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
    deployment: str = DEFAULT_DEPLOYMENT,
    request_uri: str = "/v1/whatever-deployment-id/rate",
    token_usage: dict | None = None,
    parent_deployment: str | None = DEFAULT_PARENT_DEPLOYMENT,
    trace: dict | None = default_trace(),
    execution_path: list | None = DEFAULT_EXECUTION_PATH_LIST,
    request_time: str = DEFAULT_RESPONSE_TIME,
    request_body: str | dict | None = _default_rate_request_body(),
    response_assembled: str | dict | None = None,
    response_body: str | dict | None = "whatever",
    response_upstream_uri: str | None = None,
    response_status: str = DEFAULT_RESPONSE_STATUS,
) -> dict:
    return create_message(**locals())
