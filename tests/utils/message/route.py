from tests.utils.constants import (
    DEFAULT_CHAT_ID,
    DEFAULT_DEPLOYMENT,
    DEFAULT_EXECUTION_PATH_LIST,
    DEFAULT_PARENT_DEPLOYMENT,
    DEFAULT_PROJECT_ID,
    DEFAULT_REQUEST_METHOD,
    DEFAULT_RESPONSE_STATUS,
    DEFAULT_RESPONSE_TIME,
    DEFAULT_ROUTE_PATH,
    DEFAULT_UPSTREAM_URI,
    DEFAULT_USER_ID,
    DEFAULT_USER_TITLE,
)
from tests.utils.message.base import create_message, default_trace


def create_route_message(
    *,
    chat_id: str = DEFAULT_CHAT_ID,
    project_id: str = DEFAULT_PROJECT_ID,
    user_id: str = DEFAULT_USER_ID,
    user_title: str = DEFAULT_USER_TITLE,
    deployment: str = DEFAULT_DEPLOYMENT,
    request_uri: str = f"/v1/deployments/whatever-deployment-id/route{DEFAULT_ROUTE_PATH}",
    token_usage: dict | None = None,
    parent_deployment: str | None = DEFAULT_PARENT_DEPLOYMENT,
    trace: dict | None = default_trace(),
    execution_path: list | None = DEFAULT_EXECUTION_PATH_LIST,
    request_http_method: str = DEFAULT_REQUEST_METHOD,
    request_time: str = DEFAULT_RESPONSE_TIME,
    # request body is never inspected by the analytics for route requests,
    # therefore, no need to make it realistic.
    request_body: str | dict | None = "whatever-request-body",
    # response_assembled is never inspected by the analytics for route requests,
    # therefore, no need to make it realistic.
    response_assembled: str | dict | None = "whatever-response-assembled",
    # response.body is never inspected by the analytics for mcp requests,
    # therefore, no need to make it realistic.
    response_body: str | dict | None = "whatever-response-body",
    response_upstream_uri: str | None = DEFAULT_UPSTREAM_URI,
    response_status: str = DEFAULT_RESPONSE_STATUS,
) -> dict:
    return create_message(**locals())
