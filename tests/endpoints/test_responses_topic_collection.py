import pytest

from tests.mocks import InfluxWriterMock, TopicModelEcho
from tests.utils.client import Client
from tests.utils.influx import create_responses_point
from tests.utils.message.responses import (
    create_responses_assembled_response,
    create_responses_message,
    create_responses_request,
)


@pytest.fixture
def topic_model():
    return TopicModelEcho()


def test_responses_string_input(client: Client, influx: InfluxWriterMock):
    request = create_responses_request(input="user-message")
    response = create_responses_assembled_response(content="assistant-message")
    message = create_responses_message(
        request_body=request, response_assembled=response
    )
    client(message).raise_for_status()

    point = create_responses_point(
        topic="user-message\n\nassistant-message",
    )
    influx.match_points(point)


@pytest.mark.parametrize("assembled_response", [None, "{}", "", "invalid JSON"])
def test_responses_without_assembled_response(
    client: Client, influx: InfluxWriterMock, assembled_response: str | None
):
    request = create_responses_request(input="user-message")
    message = create_responses_message(
        request_body=request, response_assembled=assembled_response
    )
    client(message).raise_for_status()

    point = create_responses_point(
        # Since there is no assembled_response.id, it's auto-generated as UUID.
        response_id="pseudo-uuid-1",
        topic="user-message",
    )
    influx.match_points(point)


def test_responses_text_content_parts(client: Client, influx: InfluxWriterMock):
    """Check that analytics collects text from the input content parts"""

    request = create_responses_request(
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": "system-message"}],
            },
            {"role": "user", "content": "user-message"},
        ]
    )
    response = create_responses_assembled_response(content="assistant-message")
    message = create_responses_message(
        request_body=request, response_assembled=response
    )
    client(message).raise_for_status()

    point = create_responses_point(
        number_request_messages=2,
        topic="system-message\n\nuser-message\n\nassistant-message",
    )
    influx.match_points(point)


def test_responses_echoed_output_content_parts(
    client: Client, influx: InfluxWriterMock
):
    """
    Check that analytics collects text from the previous turn output items
    echoed back into the input.
    """

    request = create_responses_request(
        input=[
            {"role": "user", "content": "first-user-message"},
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {"type": "output_text", "text": "first-assistant-message"}
                ],
            },
            {"role": "user", "content": "second-user-message"},
        ]
    )
    response = create_responses_assembled_response(content="assistant-message")
    message = create_responses_message(
        request_body=request, response_assembled=response
    )
    client(message).raise_for_status()

    point = create_responses_point(
        number_request_messages=3,
        topic="first-user-message\n\nfirst-assistant-message\n\nsecond-user-message\n\nassistant-message",
    )
    influx.match_points(point)


def test_responses_items_without_text_content(
    client: Client, influx: InfluxWriterMock
):
    """
    Check that analytics ignores the items without textual content, but picks
    up the function call result, which carries its text in `output`.
    """

    request = create_responses_request(
        input=[
            {"role": "user", "content": "what's the weather like?"},
            {
                "type": "function_call",
                "call_id": "call_id1",
                "name": "get_weather",
                "arguments": "{}",
            },
            {
                "type": "function_call_output",
                "call_id": "call_id1",
                "output": "It's sunny today.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": "https://example.com/image.png",
                    },
                    {"type": "input_text", "text": "user-message"},
                ],
            },
        ]
    )
    response = create_responses_assembled_response(content="assistant-message")
    message = create_responses_message(
        request_body=request, response_assembled=response
    )
    client(message).raise_for_status()

    point = create_responses_point(
        number_request_messages=4,
        topic="what's the weather like?\n\nIt's sunny today.\n\nuser-message\n\nassistant-message",
    )
    influx.match_points(point)


def test_responses_reasoning_summary_is_excluded(
    client: Client, influx: InfluxWriterMock
):
    """
    The reasoning summary of the default assembled response must not leak
    into the collected topic.
    """

    request = create_responses_request(input="user-message")
    response = create_responses_assembled_response(content="assistant-message")
    assert response["output"][0]["type"] == "reasoning"
    assert response["output"][0]["summary"][0]["text"] == "thinking"

    message = create_responses_message(
        request_body=request, response_assembled=response
    )
    client(message).raise_for_status()

    point = create_responses_point(
        topic="user-message\n\nassistant-message",
    )
    influx.match_points(point)


def test_responses_multiple_output_messages(
    client: Client, influx: InfluxWriterMock
):
    request = create_responses_request(input="user-message")
    response = create_responses_assembled_response()
    response["output"] = [
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "first-part"}],
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "second-part"}],
        },
    ]

    message = create_responses_message(
        request_body=request, response_assembled=response
    )
    client(message).raise_for_status()

    point = create_responses_point(
        topic="user-message\n\nfirst-part\n\nsecond-part",
    )
    influx.match_points(point)


def test_responses_without_chat_id(client: Client, influx: InfluxWriterMock):
    """
    Without a chat_id the content isn't analyzed at all, but unlike the
    `analytics` measurement, the topic and language tags are still written.
    """

    message = create_responses_message(chat_id="")
    client(message).raise_for_status()

    point = create_responses_point(
        chat_id="", topic="undefined", language="undefined"
    )
    influx.match_points(point)
