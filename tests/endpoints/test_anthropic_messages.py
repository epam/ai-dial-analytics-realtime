import pytest

from tests.mocks import InfluxWriterMock
from tests.utils.client import Client
from tests.utils.influx import create_anthropic_messages_point
from tests.utils.message.anthropic_messages import (
    create_anthropic_messages_assembled_response,
    create_anthropic_messages_message,
    create_anthropic_messages_request,
)
from tests.utils.message.base import on_request_body


def test_anthropic_messages_baseline(client: Client, influx: InfluxWriterMock):
    message = create_anthropic_messages_message()
    client(message).raise_for_status()
    influx.match_points(create_anthropic_messages_point())


def test_anthropic_messages_baseline_reject_non_200(
    client: Client, influx: InfluxWriterMock
):
    message = create_anthropic_messages_message(response_status="400")
    client(message).raise_for_status()
    influx.match_points()


def test_anthropic_messages_deployment(
    client: Client, influx: InfluxWriterMock
):
    message = create_anthropic_messages_message(
        deployment="test-dial-deployment-id"
    )
    client(message).raise_for_status()
    influx.match_points(
        create_anthropic_messages_point(deployment="test-dial-deployment-id")
    )


def test_anthropic_messages_model(client: Client, influx: InfluxWriterMock):
    message = create_anthropic_messages_message()

    def _set_model(body):
        body["model"] = "test-model-id"

    on_request_body(message, _set_model)

    client(message).raise_for_status()
    influx.match_points(create_anthropic_messages_point(model="test-model-id"))


def test_anthropic_messages_missing_model(
    client: Client, influx: InfluxWriterMock
):
    """
    Testing fallback to deployment when model field is missing.
    """

    message = create_anthropic_messages_message(deployment="test-deployment-id")

    def _unset_model(body):
        body.pop("model")

    on_request_body(message, _unset_model)

    client(message).raise_for_status()
    influx.match_points(
        create_anthropic_messages_point(
            deployment="test-deployment-id",
            model="test-deployment-id",
        )
    )


def test_anthropic_messages_response_id_from_assembled_response(
    client: Client, influx: InfluxWriterMock
):
    response_assembled = create_anthropic_messages_assembled_response(
        id="test-response-id"
    )
    message = create_anthropic_messages_message(
        response_assembled=response_assembled
    )
    client(message).raise_for_status()
    influx.match_points(
        create_anthropic_messages_point(response_id="test-response-id")
    )


@pytest.mark.parametrize("assembled_response", [None, "{}", "", "invalid JSON"])
def test_anthropic_messages_without_assembled_response(
    client: Client, influx: InfluxWriterMock, assembled_response: str | None
):
    message = create_anthropic_messages_message(
        response_assembled=assembled_response
    )
    client(message).raise_for_status()

    point = create_anthropic_messages_point(
        # Since there is no assembled_response.id, it's auto-generated as UUID.
        response_id="pseudo-uuid-1"
    )
    influx.match_points(point)


@pytest.mark.parametrize(
    "messages, expected_number_request_messages",
    [
        ([], 0),
        (
            [
                {"role": "user", "content": "user-message"},
                {"role": "assistant", "content": "assistant-message"},
            ],
            2,
        ),
    ],
)
def test_anthropic_messages_number_request_messages(
    client: Client,
    influx: InfluxWriterMock,
    messages: list[dict],
    expected_number_request_messages: int,
):
    request_body = create_anthropic_messages_request(messages=messages)
    message = create_anthropic_messages_message(request_body=request_body)
    client(message).raise_for_status()
    influx.match_points(
        create_anthropic_messages_point(
            number_request_messages=expected_number_request_messages
        )
    )


def test_anthropic_messages_no_request_body(
    client: Client, influx: InfluxWriterMock
):
    message = create_anthropic_messages_message(request_body=None)
    client(message).raise_for_status()
    influx.match_points(
        create_anthropic_messages_point(
            # The model falls back to the deployment when there is no body.
            model="default-deployment",
            number_request_messages=0,
        )
    )


def test_anthropic_messages_usage_from_top_level(
    client: Client, influx: InfluxWriterMock
):
    """
    The usage is always taken from the top-level `token_usage`, which DIAL Core
    reports in the Chat Completions shape for the Anthropic Messages API as
    well.
    """

    message = create_anthropic_messages_message(
        token_usage={
            "prompt_tokens": 111,
            "completion_tokens": 222,
            "total_tokens": 333,
            "prompt_tokens_details": {
                "cached_tokens": 44,
                "cache_write_tokens": 55,
            },
            "completion_tokens_details": {"reasoning_tokens": 66},
            "deployment_price": 0.001,
            "price": 0.002,
        },
    )

    client(message).raise_for_status()

    point = create_anthropic_messages_point(
        prompt_tokens=111,
        completion_tokens=222,
        cached_prompt_tokens=44,
        cache_write_prompt_tokens=55,
        reasoning_completion_tokens=66,
        deployment_price=0.001,
        price=0.002,
    )

    influx.match_points(point)


def test_anthropic_messages_price(client: Client, influx: InfluxWriterMock):
    message = create_anthropic_messages_message(
        token_usage={"deployment_price": 0.123, "price": 0.456}
    )
    client(message).raise_for_status()
    influx.match_points(
        create_anthropic_messages_point(deployment_price=0.123, price=0.456)
    )


def test_anthropic_messages_trace(client: Client, influx: InfluxWriterMock):
    trace = {
        "trace_id": "5dca3d6ed5d22b6ab574f27a6ab5ec14",
        "core_span_id": "9ade2b6fef0a716d",
        "core_parent_span_id": "20e7e64715abbe97",
    }
    message = create_anthropic_messages_message(trace=trace)
    client(message).raise_for_status()
    influx.match_points(create_anthropic_messages_point(**trace))  # type: ignore


def test_anthropic_messages_execution_path(
    client: Client, influx: InfluxWriterMock
):
    message = create_anthropic_messages_message(execution_path=["a/b", "c"])
    client(message).raise_for_status()
    influx.match_points(
        create_anthropic_messages_point(execution_path="a\\/b/c")
    )


@pytest.mark.parametrize(
    "request_uri, is_valid",
    [
        ("/anthropic/v1/messages", True),
        ("//anthropic/v1/messages", True),
        ("/anthropic/v1/messages?stream=true", True),
        # Counting tokens isn't a completion-like call.
        ("/anthropic/v1/messages/count_tokens", False),
        ("/anthropic/v2/messages", False),
        ("/openai/v1/messages", False),
        ("/openai/deployments/ID/messages", False),
    ],
)
def test_anthropic_messages_request_uri(
    caplog,
    client: Client,
    influx: InfluxWriterMock,
    request_uri: str,
    is_valid: bool,
):
    message = create_anthropic_messages_message(request_uri=request_uri)
    response = client(message).raise_for_status()
    assert response.json() == [{"status": "success"}]

    if is_valid:
        influx.match_points(create_anthropic_messages_point())
    else:
        influx.match_points()
        assert f"Unsupported message type: {request_uri!r}" in caplog.text
