import pytest

from aidial_analytics_realtime.time import parse_time
from tests.mocks import (
    InfluxWriterMock,
    LangIDNotImplemented,
    TopicModelNotImplemented,
)
from tests.utils.client import Client
from tests.utils.influx import create_mcp_point
from tests.utils.message.mcp import create_mcp_message, create_mcp_request


@pytest.fixture
def topic_model():
    return TopicModelNotImplemented()


@pytest.fixture
def language_classifier():
    return LangIDNotImplemented()


def test_mcp_baseline(client: Client, influx: InfluxWriterMock):
    message = create_mcp_message()
    client(message).raise_for_status()
    influx.match_points(create_mcp_point())


def test_mcp_baseline_reject_non_200(client: Client, influx: InfluxWriterMock):
    message = create_mcp_message(response_status="400")
    client(message).raise_for_status()
    influx.match_points()


def test_mcp_method_name(client: Client, influx: InfluxWriterMock):
    message = create_mcp_message(
        request_body=create_mcp_request(method="test-mcp-method", params={})
    )
    client(message).raise_for_status()
    influx.match_points(
        create_mcp_point(
            mcp_method="test-mcp-method",
            mcp_tool_call_name="undefined",
        )
    )


def test_mcp_tool_call_name(client: Client, influx: InfluxWriterMock):
    message = create_mcp_message(
        request_body=create_mcp_request(
            method="tools/call",
            params={
                "name": "test-tool-call-name",
                "arguments": "test-arguments",
            },
        )
    )
    client(message).raise_for_status()
    influx.match_points(
        create_mcp_point(
            mcp_method="tools/call",
            mcp_tool_call_name="test-tool-call-name",
        )
    )


def test_mcp_deployment(client: Client, influx: InfluxWriterMock):
    message = create_mcp_message(deployment="test-dial-deployment-id")
    client(message).raise_for_status()
    influx.match_points(create_mcp_point(deployment="test-dial-deployment-id"))


def test_mcp_chat_id(client: Client, influx: InfluxWriterMock):
    message = create_mcp_message(chat_id="test-chat-id")
    client(message).raise_for_status()
    influx.match_points(create_mcp_point(chat_id="test-chat-id"))


def test_mcp_project_id(client: Client, influx: InfluxWriterMock):
    message = create_mcp_message(project_id="test-project-id")
    client(message).raise_for_status()
    influx.match_points(create_mcp_point(project_id="test-project-id"))


def test_mcp_request_time(client: Client, influx: InfluxWriterMock):
    message = create_mcp_message(request_time="2023-11-24T03:33:40.39")
    client(message).raise_for_status()
    timestamp = parse_time(message["request"]["time"])
    influx.match_points(create_mcp_point(timestamp=timestamp))


def test_mcp_many_messages(client: Client, influx: InfluxWriterMock):
    n = 50
    messages = [create_mcp_message(chat_id=f"mcp-{idx}") for idx in range(0, n)]
    client(*messages).raise_for_status()

    points = [create_mcp_point(chat_id=f"mcp-{idx}") for idx in range(0, n)]
    influx.match_points(*points)


def test_mcp_parent_deployment(client: Client, influx: InfluxWriterMock):
    message = create_mcp_message(parent_deployment="test-parent-deployment")
    client(message).raise_for_status()
    influx.match_points(
        create_mcp_point(parent_deployment="test-parent-deployment")
    )


def test_mcp_trace(client: Client, influx: InfluxWriterMock):
    trace = {
        "trace_id": "5dca3d6ed5d22b6ab574f27a6ab5ec14",
        "core_span_id": "9ade2b6fef0a716d",
        "core_parent_span_id": "20e7e64715abbe97",
    }
    message = create_mcp_message(trace=trace)
    client(message).raise_for_status()
    influx.match_points(create_mcp_point(**trace))  # type: ignore


@pytest.mark.parametrize(
    "path,expected_path",
    [
        ([None, "b", "c"], "undefined/b/c"),
        (["a", "b", "c"], "a/b/c"),
        (["a/b", "c"], "a\\/b/c"),
        (["a", "b/c"], "a/b\\/c"),
    ],
)
def test_mcp_execution_path(
    client: Client, influx: InfluxWriterMock, path: list, expected_path: str
):
    message = create_mcp_message(execution_path=path)
    client(message).raise_for_status()
    influx.match_points(create_mcp_point(execution_path=expected_path))


def test_mcp_unescaped_control_char_in_message(
    client: Client, influx: InfluxWriterMock
):
    project_id = "PROJECT-\nKEY"
    response = client(
        create_mcp_message(project_id=project_id)
    ).raise_for_status()
    assert response.json() == [{"status": "success"}]

    point = create_mcp_point(project_id=project_id)
    influx.match_points(point)


@pytest.mark.parametrize(
    "request_uri, is_valid",
    [
        ("/v1/toolset/ID/mcp", True),
        ("/v1/toolset/ID1/ID2/mcp", True),
        ("/v1/toolset/ID1/ID2/mcp/abc/efg", True),
        ("/v1/toolset/ID/mpc", False),
        ("/v1/toolsets/ID/mcp", False),
    ],
)
def test_mcp_request_uri(
    caplog,
    client: Client,
    influx: InfluxWriterMock,
    request_uri: str,
    is_valid: bool,
):
    message = create_mcp_message(request_uri=request_uri)
    response = client(message).raise_for_status()
    assert response.json() == [{"status": "success"}]

    if is_valid:
        influx.match_points(create_mcp_point())
    else:
        influx.match_points()
        assert f"Unsupported message type: {request_uri!r}" in caplog.text


@pytest.mark.parametrize(
    "request_uri, is_valid",
    [
        ("/v1/deployments/ID/mcp", True),
        ("/v1/deployments/ID1/ID2/mcp", True),
        ("/v1/deployments/ID1/ID2/mcp/abc/efg", True),
        ("/v1/deployments/ID/mpc", False),
        ("/v1/deployment/ID/mcp", False),
    ],
)
def test_application_mcp_request_uri(
    caplog,
    client: Client,
    influx: InfluxWriterMock,
    request_uri: str,
    is_valid: bool,
):
    message = create_mcp_message(request_uri=request_uri)
    response = client(message).raise_for_status()
    assert response.json() == [{"status": "success"}]

    if is_valid:
        influx.match_points(create_mcp_point())
    else:
        influx.match_points()
        assert f"Unsupported message type: {request_uri!r}" in caplog.text
