from collections.abc import Callable

import pytest
from influxdb_client import Point

from tests.mocks import InfluxWriterMock
from tests.utils.client import Client
from tests.utils.constants import (
    DEFAULT_CORE_SPAN_ID,
    DEFAULT_DEPLOYMENT,
    DEFAULT_TRACE_ID,
)
from tests.utils.influx import (
    create_anthropic_messages_point,
    create_chat_point,
    create_embeddings_point,
    create_mcp_point,
    create_responses_point,
)
from tests.utils.message.anthropic_messages import (
    create_anthropic_messages_message,
)
from tests.utils.message.chat import create_chat_message
from tests.utils.message.embeddings import create_embedding_message
from tests.utils.message.mcp import create_mcp_message
from tests.utils.message.responses import create_responses_message

LOG_PREFIX = (
    f"[1/1] [trace_id={DEFAULT_TRACE_ID} span_id={DEFAULT_CORE_SPAN_ID}]"
)

INVALID_JSONS = ["", " ", "not a JSON", "{", '{"model": }', "[1, 2"]


@pytest.mark.parametrize("invalid_json", INVALID_JSONS)
@pytest.mark.parametrize(
    "create_message, expected_point, expected_error",
    [
        pytest.param(
            lambda body: create_chat_message(request_body=body),
            create_chat_point(
                model=DEFAULT_DEPLOYMENT, number_request_messages=0
            ),
            "request.body in the Chat Completions API log message isn't valid JSON",
            id="chat-request-body",
        ),
        pytest.param(
            lambda body: create_chat_message(response_assembled=body),
            create_chat_point(response_id="pseudo-uuid-1"),
            "assembled_response in the Chat Completions API log message isn't valid JSON",
            id="chat-assembled-response",
        ),
        pytest.param(
            lambda body: create_responses_message(request_body=body),
            create_responses_point(
                model=DEFAULT_DEPLOYMENT, number_request_messages=0
            ),
            "request.body in the Responses API log message isn't valid JSON",
            id="responses-request-body",
        ),
        pytest.param(
            lambda body: create_responses_message(response_assembled=body),
            create_responses_point(response_id="pseudo-uuid-1"),
            "assembled_response in the Responses API log message isn't valid JSON",
            id="responses-assembled-response",
        ),
        pytest.param(
            lambda body: create_anthropic_messages_message(request_body=body),
            create_anthropic_messages_point(
                model=DEFAULT_DEPLOYMENT, number_request_messages=0
            ),
            "request.body in the Anthropic Messages API log message isn't valid JSON",
            id="anthropic-messages-request-body",
        ),
        pytest.param(
            lambda body: create_anthropic_messages_message(
                response_assembled=body
            ),
            create_anthropic_messages_point(response_id="pseudo-uuid-1"),
            "assembled_response in the Anthropic Messages API log message isn't valid JSON",
            id="anthropic-messages-assembled-response",
        ),
        pytest.param(
            lambda body: create_embedding_message(request_body=body),
            create_embeddings_point(
                response_id="pseudo-uuid-1", number_request_messages=0
            ),
            "request.body in the Embeddings API log message isn't valid JSON",
            id="embeddings-request-body",
        ),
        pytest.param(
            lambda body: create_embedding_message(response_body=body),
            create_embeddings_point(response_id="pseudo-uuid-1"),
            "response.body in the Embeddings API log message isn't valid JSON",
            id="embeddings-response-body",
        ),
        pytest.param(
            lambda body: create_mcp_message(request_body=body),
            create_mcp_point(
                mcp_method="undefined", mcp_tool_call_name="undefined"
            ),
            "request.body in the MCP API log message isn't valid JSON",
            id="mcp-request-body",
        ),
    ],
)
def test_invalid_json_in_log_message(
    caplog,
    client: Client,
    influx: InfluxWriterMock,
    create_message: Callable[[str], dict],
    expected_point: Point,
    expected_error: str,
    invalid_json: str,
):
    response = client(create_message(invalid_json)).raise_for_status()
    assert response.json() == [{"status": "success"}]

    influx.match_points(expected_point)

    errors = [
        record.getMessage()
        for record in caplog.records
        if record.levelname == "ERROR"
    ]
    assert errors == [f"{LOG_PREFIX} {expected_error}"]
