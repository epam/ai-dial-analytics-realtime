import json

import pytest

from aidial_analytics_realtime.time import parse_time
from tests.mocks import InfluxWriterMock
from tests.utils.client import Client
from tests.utils.influx import create_point
from tests.utils.message.base import on_request_body
from tests.utils.message.chat import (
    create_chat_completion_response,
    create_chat_message,
)


def test_chat_completion_baseline(client: Client, influx: InfluxWriterMock):
    message = create_chat_message()
    client(message).raise_for_status()
    influx.match_points(create_point())


def test_chat_completion_deployment(client: Client, influx: InfluxWriterMock):
    message = create_chat_message(deployment="test-dial-deployment-id")
    client(message).raise_for_status()
    influx.match_points(create_point(deployment="test-dial-deployment-id"))


def test_chat_completion_model(client: Client, influx: InfluxWriterMock):
    message = create_chat_message()

    def _set_model(body):
        body["model"] = "test-model-id"

    on_request_body(message, _set_model)

    client(message).raise_for_status()
    influx.match_points(create_point(model="test-model-id"))


def test_chat_completion_missing_model(
    client: Client, influx: InfluxWriterMock
):
    """
    Testing fallback to deployment when model field is missing.
    """

    message = create_chat_message(deployment="test-deployment-id")

    def _unset_model(body):
        body.pop("model")

    on_request_body(message, _unset_model)

    client(message).raise_for_status()
    influx.match_points(
        create_point(
            deployment="test-deployment-id",
            model="test-deployment-id",
        )
    )


def test_chat_completion_chat_id(client: Client, influx: InfluxWriterMock):
    message = create_chat_message(chat_id="test-chat-id")
    client(message).raise_for_status()
    influx.match_points(create_point(chat_id="test-chat-id"))


def test_chat_completion_project_id(client: Client, influx: InfluxWriterMock):
    message = create_chat_message(project_id="test-project-id")
    client(message).raise_for_status()
    influx.match_points(create_point(project_id="test-project-id"))


def test_chat_completion_request_time(client: Client, influx: InfluxWriterMock):
    message = create_chat_message(request_time="2023-11-24T03:33:40.39")
    client(message).raise_for_status()
    timestamp = parse_time(message["request"]["time"])
    influx.match_points(create_point(timestamp=timestamp))


def test_chat_completion_response_id_from_assembled_response(
    client: Client, influx: InfluxWriterMock
):
    response_assembled = create_chat_completion_response(id="test-response-id")
    message = create_chat_message(response_assembled=response_assembled)
    client(message).raise_for_status()
    influx.match_points(create_point(response_id="test-response-id"))


def test_chat_completion_many_messages(
    client: Client, influx: InfluxWriterMock
):
    n = 50
    messages = [
        create_chat_message(chat_id=f"chat-{idx}") for idx in range(0, n)
    ]
    client(*messages).raise_for_status()

    points = [create_point(chat_id=f"chat-{idx}") for idx in range(0, n)]
    influx.match_points(*points)


def test_chat_completion_usage_from_response(
    client: Client, influx: InfluxWriterMock
):
    """
    Checking that the usage is taken from the response
    when the top-level usage isn't provided.
    """

    response = create_chat_completion_response()
    message = create_chat_message(token_usage=None, response_assembled=response)
    client(message).raise_for_status()

    usage = response["usage"]
    point = create_point(
        price=0.0,
        deployment_price=0.0,
        prompt_tokens=usage["prompt_tokens"],
        completion_tokens=usage["completion_tokens"],
        cached_prompt_tokens=usage["prompt_tokens_details"]["cached_tokens"],
    )

    influx.match_points(point)


def test_chat_completion_usage_from_top_level(
    client: Client, influx: InfluxWriterMock
):
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

    point = create_point(
        prompt_tokens=111,
        completion_tokens=222,
        cached_prompt_tokens=44,
        deployment_price=0.001,
        price=0.002,
    )

    influx.match_points(point)


def test_chat_completion_text_content_parts(
    client: Client, influx: InfluxWriterMock
):
    """Check that analytics collects text content from text content parts"""

    request_body = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "system",
                "content": [{"type": "text", "text": "be nice"}],
            },
            {"role": "user", "content": "ping?"},
        ],
    }

    message = create_chat_message(request_body=request_body)

    client(message).raise_for_status()

    point = create_point(topic="be nice\n\nping?\n\npong")
    influx.match_points(point)


def test_chat_completion_messages_without_text_content(
    client: Client, influx: InfluxWriterMock
):
    """Check that analytics ignores content parts without textual content"""

    message = create_chat_message()
    message["request"]["body"] = json.dumps(
        {
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "what's the weather like?"},
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "tool_call_id1",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": {},
                            },
                        }
                    ],
                },
                {
                    "role": "tool",
                    "id": "tool_call_id1",
                    "content": "It's sunny today.",
                },
                {"role": "user", "content": "ping?"},
            ],
        }
    )

    client(message).raise_for_status()

    point = create_point(
        number_request_messages=4,
        topic="what's the weather like?\n\nIt's sunny today.\n\nping?\n\npong",
    )

    influx.match_points(point)


def test_chat_completion_parent_deployment(
    client: Client, influx: InfluxWriterMock
):
    message = create_chat_message(parent_deployment="test-parent-deployment")
    client(message).raise_for_status()
    influx.match_points(
        create_point(parent_deployment="test-parent-deployment")
    )


def test_chat_completion_trace(client: Client, influx: InfluxWriterMock):
    message = create_chat_message(
        trace={
            "trace_id": "5dca3d6ed5d22b6ab574f27a6ab5ec14",
            "core_span_id": "9ade2b6fef0a716d",
            "core_parent_span_id": "20e7e64715abbe97",
        }
    )
    client(message).raise_for_status()
    influx.match_points(
        create_point(
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
def test_chat_completion_execution_path(
    client: Client, influx: InfluxWriterMock, path: list, expected_path: str
):
    message = create_chat_message(execution_path=path)
    client(message).raise_for_status()
    influx.match_points(create_point(execution_path=expected_path))


def test_chat_completion_price(client: Client, influx: InfluxWriterMock):
    message = create_chat_message(token_usage={"price": 0.456})
    client(message).raise_for_status()
    influx.match_points(create_point(price=0.456))


def test_chat_completion_deployment_price_no_price(
    client: Client, influx: InfluxWriterMock
):
    message = create_chat_message(token_usage={"deployment_price": 0.123})
    client(message).raise_for_status()
    influx.match_points(create_point(deployment_price=0.0))


def test_chat_completion_deployment_price_with_price(
    client: Client, influx: InfluxWriterMock
):
    message = create_chat_message(
        token_usage={"deployment_price": 0.123, "price": 0.456}
    )
    client(message).raise_for_status()
    influx.match_points(create_point(deployment_price=0.123, price=0.456))


@pytest.mark.parametrize("assembled_response", [None, "{}", "", "invalid JSON"])
def test_chat_completion_invalid_assembled_response(
    client: Client,
    influx: InfluxWriterMock,
    assembled_response: str | None,
):
    message = create_chat_message(response_assembled=assembled_response)
    client(message).raise_for_status()

    point = create_point(
        # Since there is no assembled_response.id, it's auto-generated as UUID.
        response_id="pseudo-uuid-1",
        topic="ping?",
        prompt_tokens=0,
        completion_tokens=0,
        deployment_price=0.0,
        price=0.0,
    )
    influx.match_points(point)


def test_unescaped_control_char_in_message(
    client: Client, influx: InfluxWriterMock
):
    response = client(
        create_chat_message(project_id="PROJECT-\nKEY")
    ).raise_for_status()
    assert response.json() == [{"status": "success"}]

    point = create_point(project_id="PROJECT-\nKEY")
    influx.match_points(point)
