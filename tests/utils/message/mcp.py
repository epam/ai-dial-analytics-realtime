from tests.utils.constants import (
    DEFAULT_CHAT_ID,
    DEFAULT_DEPLOYMENT,
    DEFAULT_EXECUTION_PATH_LIST,
    DEFAULT_MCP_METHOD,
    DEFAULT_MCP_TOOL_CALL_NAME,
    DEFAULT_PARENT_DEPLOYMENT,
    DEFAULT_PROJECT_ID,
    DEFAULT_RESPONSE_STATUS,
    DEFAULT_RESPONSE_TIME,
    DEFAULT_UPSTREAM_URI,
    DEFAULT_USER_ID,
    DEFAULT_USER_TITLE,
)
from tests.utils.message.base import create_message, default_trace


def _create_mcp_params(
    *, name: str = DEFAULT_MCP_TOOL_CALL_NAME, arguments: dict = {}
) -> dict:
    return {"name": name, "arguments": arguments}


def create_mcp_request(
    *, method: str = DEFAULT_MCP_METHOD, params: dict = _create_mcp_params()
):
    return {"jsonrpc": "2.0", "id": 0, "method": method, "params": params}


def create_mcp_tool_list_request():
    return create_mcp_request(method="tools/list", params={})


def create_mcp_message(
    *,
    chat_id: str = DEFAULT_CHAT_ID,
    project_id: str = DEFAULT_PROJECT_ID,
    user_id: str = DEFAULT_USER_ID,
    user_title: str = DEFAULT_USER_TITLE,
    deployment: str = DEFAULT_DEPLOYMENT,
    request_uri: str = "/v1/toolset/whatever-deployment-id/mcp",
    token_usage: dict | None = None,
    parent_deployment: str | None = DEFAULT_PARENT_DEPLOYMENT,
    trace: dict | None = default_trace(),
    execution_path: list | None = DEFAULT_EXECUTION_PATH_LIST,
    request_time: str = DEFAULT_RESPONSE_TIME,
    request_body: str | dict | None = create_mcp_request(),
    # response_assembled is never inspected by the analytics for mcp requests,
    # therefore, no need to make it realistic.
    response_assembled: str | dict | None = "whatever-response-assembled",
    # response.body is never inspected by the analytics for mcp requests,
    # therefore, no need to make it realistic.
    response_body: str | dict | None = "whatever-response-body",
    response_upstream_uri: str | None = DEFAULT_UPSTREAM_URI,
    response_status: str = DEFAULT_RESPONSE_STATUS,
) -> dict:
    return create_message(**locals())
