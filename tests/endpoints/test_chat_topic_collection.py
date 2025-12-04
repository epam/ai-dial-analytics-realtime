import pytest

from tests.mocks import InfluxWriterMock, TopicModelEcho
from tests.utils.client import Client
from tests.utils.influx import create_point
from tests.utils.message.chat import (
    create_assembled_response,
    create_chat_message,
    create_request,
)


@pytest.fixture
def topic_model():
    return TopicModelEcho()


@pytest.mark.parametrize("assembled_response", [None, "{}", "", "invalid JSON"])
def test_chat_completion_without_assembled_response(
    client: Client,
    influx: InfluxWriterMock,
    assembled_response: str | None,
):
    request = create_request("user-message")
    message = create_chat_message(
        request_body=request, response_assembled=assembled_response
    )
    client(message).raise_for_status()

    point = create_point(
        # Since there is no assembled_response.id, it's auto-generated as UUID.
        response_id="pseudo-uuid-1",
        topic="user-message",
        prompt_tokens=0,
        completion_tokens=0,
        deployment_price=0.0,
        price=0.0,
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
                "content": [{"type": "text", "text": "system-message"}],
            },
            {"role": "user", "content": "user-message"},
        ],
    }

    response = create_assembled_response(content="assistant-message")
    message = create_chat_message(
        request_body=request_body, response_assembled=response
    )

    client(message).raise_for_status()

    point = create_point(
        number_request_messages=2,
        topic="system-message\n\nuser-message\n\nassistant-message",
    )
    influx.match_points(point)


def test_chat_completion_messages_without_text_content(
    client: Client, influx: InfluxWriterMock
):
    """Check that analytics ignores content parts without textual content"""

    request_body = {
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
            {"role": "user", "content": "user-message"},
        ],
    }

    response = create_assembled_response(content="assistant-message")
    message = create_chat_message(
        request_body=request_body, response_assembled=response
    )
    client(message).raise_for_status()

    point = create_point(
        number_request_messages=4,
        topic="what's the weather like?\n\nIt's sunny today.\n\nuser-message\n\nassistant-message",
    )

    influx.match_points(point)
