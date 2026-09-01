import pytest

from tests.mocks import InfluxWriterMock
from tests.utils.client import Client
from tests.utils.influx import create_responses_point
from tests.utils.message.base import on_request_body
from tests.utils.message.responses import (
    create_responses_assembled_response,
    create_responses_message,
    create_responses_request,
)


def test_responses_baseline(client: Client, influx: InfluxWriterMock):
    message = create_responses_message()
    client(message).raise_for_status()
    influx.match_points(create_responses_point())


def test_responses_baseline_reject_non_200(
    client: Client, influx: InfluxWriterMock
):
    message = create_responses_message(response_status="400")
    client(message).raise_for_status()
    influx.match_points()


def test_responses_deployment(client: Client, influx: InfluxWriterMock):
    message = create_responses_message(deployment="test-dial-deployment-id")
    client(message).raise_for_status()
    influx.match_points(
        create_responses_point(deployment="test-dial-deployment-id")
    )


def test_responses_model(client: Client, influx: InfluxWriterMock):
    message = create_responses_message()

    def _set_model(body):
        body["model"] = "test-model-id"

    on_request_body(message, _set_model)

    client(message).raise_for_status()
    influx.match_points(create_responses_point(model="test-model-id"))


def test_responses_missing_model(client: Client, influx: InfluxWriterMock):
    """
    Testing fallback to deployment when model field is missing.
    """

    message = create_responses_message(deployment="test-deployment-id")

    def _unset_model(body):
        body.pop("model")

    on_request_body(message, _unset_model)

    client(message).raise_for_status()
    influx.match_points(
        create_responses_point(
            deployment="test-deployment-id",
            model="test-deployment-id",
        )
    )


def test_responses_response_id_from_assembled_response(
    client: Client, influx: InfluxWriterMock
):
    response_assembled = create_responses_assembled_response(
        id="test-response-id"
    )
    message = create_responses_message(response_assembled=response_assembled)
    client(message).raise_for_status()
    influx.match_points(create_responses_point(response_id="test-response-id"))


@pytest.mark.parametrize("assembled_response", [None, "{}", "", "invalid JSON"])
def test_responses_without_assembled_response(
    client: Client, influx: InfluxWriterMock, assembled_response: str | None
):
    message = create_responses_message(response_assembled=assembled_response)
    client(message).raise_for_status()

    point = create_responses_point(
        # Since there is no assembled_response.id, it's auto-generated as UUID.
        response_id="pseudo-uuid-1"
    )
    influx.match_points(point)


@pytest.mark.parametrize(
    "input, expected_number_request_messages",
    [
        ("a single string input", 1),
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
def test_responses_number_request_messages(
    client: Client,
    influx: InfluxWriterMock,
    input: str | list,
    expected_number_request_messages: int,
):
    request_body = create_responses_request(input=input)
    message = create_responses_message(request_body=request_body)
    client(message).raise_for_status()
    influx.match_points(
        create_responses_point(
            number_request_messages=expected_number_request_messages
        )
    )


def test_responses_no_request_body(client: Client, influx: InfluxWriterMock):
    message = create_responses_message(request_body=None)
    client(message).raise_for_status()
    influx.match_points(
        create_responses_point(
            # The model falls back to the deployment when there is no body.
            model="default-deployment",
            number_request_messages=0,
        )
    )


def test_responses_usage_from_top_level(
    client: Client, influx: InfluxWriterMock
):
    """
    The usage is always taken from the top-level `token_usage`, which DIAL Core
    reports in the Chat Completions shape for the Responses API as well.
    """

    message = create_responses_message(
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

    point = create_responses_point(
        prompt_tokens=111,
        completion_tokens=222,
        cached_prompt_tokens=44,
        cache_write_prompt_tokens=55,
        reasoning_completion_tokens=66,
        deployment_price=0.001,
        price=0.002,
    )

    influx.match_points(point)


def test_responses_price(client: Client, influx: InfluxWriterMock):
    message = create_responses_message(
        token_usage={"deployment_price": 0.123, "price": 0.456}
    )
    client(message).raise_for_status()
    influx.match_points(
        create_responses_point(deployment_price=0.123, price=0.456)
    )


def test_responses_trace(client: Client, influx: InfluxWriterMock):
    trace = {
        "trace_id": "5dca3d6ed5d22b6ab574f27a6ab5ec14",
        "core_span_id": "9ade2b6fef0a716d",
        "core_parent_span_id": "20e7e64715abbe97",
    }
    message = create_responses_message(trace=trace)
    client(message).raise_for_status()
    influx.match_points(create_responses_point(**trace))  # type: ignore


def test_responses_execution_path(client: Client, influx: InfluxWriterMock):
    message = create_responses_message(execution_path=["a/b", "c"])
    client(message).raise_for_status()
    influx.match_points(create_responses_point(execution_path="a\\/b/c"))


@pytest.mark.parametrize(
    "request_uri, is_valid",
    [
        ("/openai/v1/responses", True),
        ("//openai/v1/responses", True),
        ("/openai/v1/responses?stream=true", True),
        # Retrieve/delete/cancel a response by ID aren't completion-like calls.
        ("/openai/v1/responses/RESPONSE_ID", False),
        ("/openai/v1/responses/RESPONSE_ID/cancel", False),
        ("/openai/v2/responses", False),
        ("/openai/deployments/ID/responses", False),
    ],
)
def test_responses_request_uri(
    caplog,
    client: Client,
    influx: InfluxWriterMock,
    request_uri: str,
    is_valid: bool,
):
    message = create_responses_message(request_uri=request_uri)
    response = client(message).raise_for_status()
    assert response.json() == [{"status": "success"}]

    if is_valid:
        influx.match_points(create_responses_point())
    else:
        influx.match_points()
        assert f"Unsupported message type: {request_uri!r}" in caplog.text
