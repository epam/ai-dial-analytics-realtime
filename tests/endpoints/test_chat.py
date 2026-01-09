import pytest

from aidial_analytics_realtime.time import parse_time
from tests.mocks import InfluxWriterMock
from tests.utils.client import Client
from tests.utils.influx import create_chat_point
from tests.utils.message.base import on_request_body
from tests.utils.message.chat import (
    create_chat_assembled_response,
    create_chat_message,
)


def test_chat_baseline(client: Client, influx: InfluxWriterMock):
    message = create_chat_message()
    client(message).raise_for_status()
    influx.match_points(create_chat_point())


def test_chat_deployment(client: Client, influx: InfluxWriterMock):
    message = create_chat_message(deployment="test-dial-deployment-id")
    client(message).raise_for_status()
    influx.match_points(create_chat_point(deployment="test-dial-deployment-id"))


def test_chat_model(client: Client, influx: InfluxWriterMock):
    message = create_chat_message()

    def _set_model(body):
        body["model"] = "test-model-id"

    on_request_body(message, _set_model)

    client(message).raise_for_status()
    influx.match_points(create_chat_point(model="test-model-id"))


def test_chat_missing_model(client: Client, influx: InfluxWriterMock):
    """
    Testing fallback to deployment when model field is missing.
    """

    message = create_chat_message(deployment="test-deployment-id")

    def _unset_model(body):
        body.pop("model")

    on_request_body(message, _unset_model)

    client(message).raise_for_status()
    influx.match_points(
        create_chat_point(
            deployment="test-deployment-id",
            model="test-deployment-id",
        )
    )


def test_chat_chat_id(client: Client, influx: InfluxWriterMock):
    message = create_chat_message(chat_id="test-chat-id")
    client(message).raise_for_status()
    influx.match_points(create_chat_point(chat_id="test-chat-id"))


def test_chat_project_id(client: Client, influx: InfluxWriterMock):
    message = create_chat_message(project_id="test-project-id")
    client(message).raise_for_status()
    influx.match_points(create_chat_point(project_id="test-project-id"))


def test_chat_request_time(client: Client, influx: InfluxWriterMock):
    message = create_chat_message(request_time="2023-11-24T03:33:40.39")
    client(message).raise_for_status()
    timestamp = parse_time(message["request"]["time"])
    influx.match_points(create_chat_point(timestamp=timestamp))


def test_chat_response_id_from_assembled_response(
    client: Client, influx: InfluxWriterMock
):
    response_assembled = create_chat_assembled_response(id="test-response-id")
    message = create_chat_message(response_assembled=response_assembled)
    client(message).raise_for_status()
    influx.match_points(create_chat_point(response_id="test-response-id"))


def test_chat_many_messages(client: Client, influx: InfluxWriterMock):
    n = 50
    messages = [
        create_chat_message(chat_id=f"chat-{idx}") for idx in range(0, n)
    ]
    client(*messages).raise_for_status()

    points = [create_chat_point(chat_id=f"chat-{idx}") for idx in range(0, n)]
    influx.match_points(*points)


def test_chat_usage_from_response(client: Client, influx: InfluxWriterMock):
    """
    Checking that the usage is taken from the response
    when the top-level usage isn't provided.
    """

    response = create_chat_assembled_response()
    message = create_chat_message(token_usage=None, response_assembled=response)
    client(message).raise_for_status()

    usage = response["usage"]
    point = create_chat_point(
        price=0.0,
        deployment_price=0.0,
        prompt_tokens=usage["prompt_tokens"],
        completion_tokens=usage["completion_tokens"],
        cached_prompt_tokens=usage["prompt_tokens_details"]["cached_tokens"],
    )

    influx.match_points(point)


def test_chat_usage_from_top_level(client: Client, influx: InfluxWriterMock):
    """
    Checking that the usage is taken from top level usage if it's provided.
    """

    message = create_chat_message(
        token_usage={
            "prompt_tokens": 111,
            "completion_tokens": 222,
            "total_tokens": 333,
            "prompt_tokens_details": {"cached_tokens": 44},
            "deployment_price": 0.001,
            "price": 0.002,
        },
    )

    client(message).raise_for_status()

    point = create_chat_point(
        prompt_tokens=111,
        completion_tokens=222,
        cached_prompt_tokens=44,
        deployment_price=0.001,
        price=0.002,
    )

    influx.match_points(point)


def test_chat_parent_deployment(client: Client, influx: InfluxWriterMock):
    message = create_chat_message(parent_deployment="test-parent-deployment")
    client(message).raise_for_status()
    influx.match_points(
        create_chat_point(parent_deployment="test-parent-deployment")
    )


def test_chat_trace(client: Client, influx: InfluxWriterMock):
    message = create_chat_message(
        trace={
            "trace_id": "5dca3d6ed5d22b6ab574f27a6ab5ec14",
            "core_span_id": "9ade2b6fef0a716d",
            "core_parent_span_id": "20e7e64715abbe97",
        }
    )
    client(message).raise_for_status()
    influx.match_points(
        create_chat_point(
            trace_id="5dca3d6ed5d22b6ab574f27a6ab5ec14",
            core_span_id="9ade2b6fef0a716d",
            core_parent_span_id="20e7e64715abbe97",
        )
    )


@pytest.mark.parametrize(
    "path,expected_path",
    [
        ([None, "b", "c"], "undefined/b/c"),
        (["a", "b", "c"], "a/b/c"),
    ],
)
def test_chat_execution_path(
    client: Client, influx: InfluxWriterMock, path: list, expected_path: str
):
    message = create_chat_message(execution_path=path)
    client(message).raise_for_status()
    influx.match_points(create_chat_point(execution_path=expected_path))


def test_chat_price(client: Client, influx: InfluxWriterMock):
    message = create_chat_message(token_usage={"price": 0.456})
    client(message).raise_for_status()
    influx.match_points(create_chat_point(price=0.456))


def test_chat_deployment_price_no_price(
    client: Client, influx: InfluxWriterMock
):
    message = create_chat_message(token_usage={"deployment_price": 0.123})
    client(message).raise_for_status()
    influx.match_points(create_chat_point(deployment_price=0.0))


def test_chat_deployment_price_with_price(
    client: Client, influx: InfluxWriterMock
):
    message = create_chat_message(
        token_usage={"deployment_price": 0.123, "price": 0.456}
    )
    client(message).raise_for_status()
    influx.match_points(create_chat_point(deployment_price=0.123, price=0.456))


@pytest.mark.parametrize("assembled_response", [None, "{}", "", "invalid JSON"])
def test_chat_without_assembled_response(
    client: Client,
    influx: InfluxWriterMock,
    assembled_response: str | None,
):
    message = create_chat_message(response_assembled=assembled_response)
    client(message).raise_for_status()

    point = create_chat_point(
        # Since there is no assembled_response.id, it's auto-generated as UUID.
        response_id="pseudo-uuid-1",
        prompt_tokens=0,
        completion_tokens=0,
        deployment_price=0.0,
        price=0.0,
    )
    influx.match_points(point)


def test_chat_unescaped_control_char_in_message(
    client: Client, influx: InfluxWriterMock
):
    project_id = "PROJECT-\nKEY"
    response = client(
        create_chat_message(project_id=project_id)
    ).raise_for_status()
    assert response.json() == [{"status": "success"}]

    point = create_chat_point(project_id=project_id)
    influx.match_points(point)


@pytest.mark.parametrize(
    "request_uri, is_valid",
    [
        ("/openai/deployments/ID/chat/completions", True),
        ("/openai/deployments/ID1/ID2/chat/completions", True),
        ("/openai/deployments/ID/chat/completions/abc/efg", True),
        ("/openai/deployments/ID/completions", False),
        ("/openai/ID/chat/completions", False),
    ],
)
def test_chat_request_uri(
    caplog,
    client: Client,
    influx: InfluxWriterMock,
    request_uri: str,
    is_valid: bool,
):
    message = create_chat_message(request_uri=request_uri)
    response = client(message).raise_for_status()
    assert response.json() == [{"status": "success"}]

    if is_valid:
        influx.match_points(create_chat_point())
    else:
        influx.match_points()
        assert f"Unsupported message type: {request_uri!r}" in caplog.text
