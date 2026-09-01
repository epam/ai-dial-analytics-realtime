import pytest

from tests.mocks import InfluxWriterMock, TopicModelEcho
from tests.utils.client import Client
from tests.utils.influx import create_anthropic_messages_point
from tests.utils.message.anthropic_messages import (
    create_anthropic_messages_assembled_response,
    create_anthropic_messages_message,
    create_anthropic_messages_request,
)


@pytest.fixture
def topic_model():
    return TopicModelEcho()


def test_anthropic_messages_string_content(
    client: Client, influx: InfluxWriterMock
):
    request = create_anthropic_messages_request(
        messages=[{"role": "user", "content": "user-message"}]
    )
    response = create_anthropic_messages_assembled_response(
        content="assistant-message"
    )
    message = create_anthropic_messages_message(
        request_body=request, response_assembled=response
    )
    client(message).raise_for_status()

    point = create_anthropic_messages_point(
        topic="user-message\n\nassistant-message",
    )
    influx.match_points(point)


@pytest.mark.parametrize("assembled_response", [None, "{}", "", "invalid JSON"])
def test_anthropic_messages_without_assembled_response(
    client: Client, influx: InfluxWriterMock, assembled_response: str | None
):
    request = create_anthropic_messages_request(
        messages=[{"role": "user", "content": "user-message"}]
    )
    message = create_anthropic_messages_message(
        request_body=request, response_assembled=assembled_response
    )
    client(message).raise_for_status()

    point = create_anthropic_messages_point(
        # Since there is no assembled_response.id, it's auto-generated as UUID.
        response_id="pseudo-uuid-1",
        topic="user-message",
    )
    influx.match_points(point)


def test_anthropic_messages_text_content_blocks(
    client: Client, influx: InfluxWriterMock
):
    """Check that analytics collects text from the message content blocks"""

    request = create_anthropic_messages_request(
        messages=[
            {
                "role": "user",
                "content": [{"type": "text", "text": "first-user-message"}],
            },
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "first-assistant-message"}
                ],
            },
            {"role": "user", "content": "second-user-message"},
        ]
    )
    response = create_anthropic_messages_assembled_response(
        content="assistant-message"
    )
    message = create_anthropic_messages_message(
        request_body=request, response_assembled=response
    )
    client(message).raise_for_status()

    point = create_anthropic_messages_point(
        number_request_messages=3,
        topic="first-user-message\n\nfirst-assistant-message\n\nsecond-user-message\n\nassistant-message",
    )
    influx.match_points(point)


@pytest.mark.parametrize(
    "system",
    [
        "system-prompt",
        [{"type": "text", "text": "system-prompt"}],
    ],
)
def test_anthropic_messages_system_prompt(
    client: Client, influx: InfluxWriterMock, system: str | list
):
    """
    The system prompt is a top-level field rather than a message with the
    "system" role, but it's collected all the same.
    """

    request = create_anthropic_messages_request(
        messages=[{"role": "user", "content": "user-message"}]
    )
    request["system"] = system

    response = create_anthropic_messages_assembled_response(
        content="assistant-message"
    )
    message = create_anthropic_messages_message(
        request_body=request, response_assembled=response
    )
    client(message).raise_for_status()

    point = create_anthropic_messages_point(
        topic="system-prompt\n\nuser-message\n\nassistant-message",
    )
    influx.match_points(point)


def test_anthropic_messages_blocks_without_text_content(
    client: Client, influx: InfluxWriterMock
):
    """
    Check that analytics ignores the content blocks without textual content,
    but picks up the tool result, which carries its text in a nested `content`.
    """

    request = create_anthropic_messages_request(
        messages=[
            {"role": "user", "content": "what's the weather like?"},
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_id1",
                        "name": "get_weather",
                        "input": {},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_id1",
                        "content": "It's sunny today.",
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "url",
                            "url": "https://example.com/image.png",
                        },
                    },
                    {"type": "text", "text": "user-message"},
                ],
            },
        ]
    )
    response = create_anthropic_messages_assembled_response(
        content="assistant-message"
    )
    message = create_anthropic_messages_message(
        request_body=request, response_assembled=response
    )
    client(message).raise_for_status()

    point = create_anthropic_messages_point(
        number_request_messages=4,
        topic="what's the weather like?\n\nIt's sunny today.\n\nuser-message\n\nassistant-message",
    )
    influx.match_points(point)


def test_anthropic_messages_tool_result_content_blocks(
    client: Client, influx: InfluxWriterMock
):
    """
    A tool result content may itself be a list of the content blocks.
    """

    request = create_anthropic_messages_request(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_id1",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "url",
                                    "url": "https://example.com/image.png",
                                },
                            },
                            {"type": "text", "text": "It's sunny today."},
                        ],
                    }
                ],
            },
        ]
    )
    response = create_anthropic_messages_assembled_response(
        content="assistant-message"
    )
    message = create_anthropic_messages_message(
        request_body=request, response_assembled=response
    )
    client(message).raise_for_status()

    point = create_anthropic_messages_point(
        topic="It's sunny today.\n\nassistant-message",
    )
    influx.match_points(point)


def test_anthropic_messages_thinking_is_excluded(
    client: Client, influx: InfluxWriterMock
):
    """
    The thinking block of the default assembled response must not leak
    into the collected topic.
    """

    request = create_anthropic_messages_request(
        messages=[{"role": "user", "content": "user-message"}]
    )
    response = create_anthropic_messages_assembled_response(
        content="assistant-message"
    )
    assert response["content"][0]["type"] == "thinking"
    assert response["content"][0]["thinking"] == "thinking"

    message = create_anthropic_messages_message(
        request_body=request, response_assembled=response
    )
    client(message).raise_for_status()

    point = create_anthropic_messages_point(
        topic="user-message\n\nassistant-message",
    )
    influx.match_points(point)


def test_anthropic_messages_multiple_output_text_blocks(
    client: Client, influx: InfluxWriterMock
):
    request = create_anthropic_messages_request(
        messages=[{"role": "user", "content": "user-message"}]
    )
    response = create_anthropic_messages_assembled_response()
    response["content"] = [
        {"type": "text", "text": "first-part"},
        {"type": "text", "text": "second-part"},
    ]

    message = create_anthropic_messages_message(
        request_body=request, response_assembled=response
    )
    client(message).raise_for_status()

    point = create_anthropic_messages_point(
        topic="user-message\n\nfirst-part\n\nsecond-part",
    )
    influx.match_points(point)


def test_anthropic_messages_without_chat_id(
    client: Client, influx: InfluxWriterMock
):
    """
    Without a chat_id the content isn't analyzed at all, but unlike the
    `analytics` measurement, the topic and language tags are still written.
    """

    message = create_anthropic_messages_message(chat_id="")
    client(message).raise_for_status()

    point = create_anthropic_messages_point(
        chat_id="", topic="undefined", language="undefined"
    )
    influx.match_points(point)
