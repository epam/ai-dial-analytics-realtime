import pytest

from aidial_analytics_realtime.time import parse_time
from tests.mocks import (
    InfluxWriterMock,
    LangIDNotImplemented,
    TopicModelNotImplemented,
)
from tests.utils.client import Client
from tests.utils.influx import create_route_point
from tests.utils.message.route import create_route_message


@pytest.fixture
def topic_model():
    return TopicModelNotImplemented()


@pytest.fixture
def language_classifier():
    return LangIDNotImplemented()


def test_route_baseline(client: Client, influx: InfluxWriterMock):
    message = create_route_message()
    client(message).raise_for_status()
    influx.match_points(create_route_point())


def test_route_baseline_reject_non_200(
    client: Client, influx: InfluxWriterMock
):
    message = create_route_message(response_status="400")
    client(message).raise_for_status()
    influx.match_points()


@pytest.mark.parametrize("http_method", ["GET", "POST", "PATCH", "DELETE"])
def test_route_http_method(
    client: Client, influx: InfluxWriterMock, http_method: str
):
    message = create_route_message(request_http_method=http_method)
    client(message).raise_for_status()
    influx.match_points(create_route_point(http_method=http_method))


def test_route_deployment(client: Client, influx: InfluxWriterMock):
    message = create_route_message(deployment="test-dial-deployment-id")
    client(message).raise_for_status()
    influx.match_points(
        create_route_point(deployment="test-dial-deployment-id")
    )


def test_route_chat_id(client: Client, influx: InfluxWriterMock):
    message = create_route_message(chat_id="test-chat-id")
    client(message).raise_for_status()
    influx.match_points(create_route_point(chat_id="test-chat-id"))


def test_route_project_id(client: Client, influx: InfluxWriterMock):
    message = create_route_message(project_id="test-project-id")
    client(message).raise_for_status()
    influx.match_points(create_route_point(project_id="test-project-id"))


def test_route_request_time(client: Client, influx: InfluxWriterMock):
    message = create_route_message(request_time="2023-11-24T03:33:40.39")
    client(message).raise_for_status()
    timestamp = parse_time(message["request"]["time"])
    influx.match_points(create_route_point(timestamp=timestamp))


def test_route_many_messages(client: Client, influx: InfluxWriterMock):
    n = 50
    messages = [
        create_route_message(chat_id=f"mcp-{idx}") for idx in range(0, n)
    ]
    client(*messages).raise_for_status()

    points = [create_route_point(chat_id=f"mcp-{idx}") for idx in range(0, n)]
    influx.match_points(*points)


def test_route_parent_deployment(client: Client, influx: InfluxWriterMock):
    message = create_route_message(parent_deployment="test-parent-deployment")
    client(message).raise_for_status()
    influx.match_points(
        create_route_point(parent_deployment="test-parent-deployment")
    )


def test_route_trace(client: Client, influx: InfluxWriterMock):
    trace = {
        "trace_id": "5dca3d6ed5d22b6ab574f27a6ab5ec14",
        "core_span_id": "9ade2b6fef0a716d",
        "core_parent_span_id": "20e7e64715abbe97",
    }
    message = create_route_message(trace=trace)
    client(message).raise_for_status()
    influx.match_points(create_route_point(**trace))  # type: ignore


@pytest.mark.parametrize(
    "path,expected_path",
    [
        ([None, "b", "c"], "undefined/b/c"),
        (["a", "b", "c"], "a/b/c"),
    ],
)
def test_route_execution_path(
    client: Client, influx: InfluxWriterMock, path: list, expected_path: str
):
    message = create_route_message(execution_path=path)
    client(message).raise_for_status()
    influx.match_points(create_route_point(execution_path=expected_path))


def test_route_unescaped_control_char_in_message(
    client: Client, influx: InfluxWriterMock
):
    project_id = "PROJECT-\nKEY"
    response = client(
        create_route_message(project_id=project_id)
    ).raise_for_status()
    assert response.json() == [{"status": "success"}]

    point = create_route_point(project_id=project_id)
    influx.match_points(point)


@pytest.mark.parametrize(
    "request_uri, route_path",
    [
        ("/v1/deployments/ID/route/PATH1", "/PATH1"),
        ("/v1/deployments/ID/route/PATH1/PATH2", "/PATH1/PATH2"),
        ("/v1/deployments/ID1/ID2/route/PATH1/PATH2", "/PATH1/PATH2"),
        ("/v1/deployments/ID1/ID2/routes/PATH1", None),
        ("/v1/deployment/ID1/ID2/route/PATH1", None),
    ],
)
def test_route_request_uri(
    caplog,
    client: Client,
    influx: InfluxWriterMock,
    request_uri: str,
    route_path: str | None,
):
    message = create_route_message(request_uri=request_uri)
    response = client(message).raise_for_status()
    assert response.json() == [{"status": "success"}]

    if route_path is not None:
        influx.match_points(create_route_point(route=route_path))
    else:
        influx.match_points()
        assert f"Unsupported message type: {request_uri!r}" in caplog.text
