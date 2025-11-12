import json
import re
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import aidial_analytics_realtime.app as app
from aidial_analytics_realtime.time import parse_time
from tests.mocks import InfluxWriterMock, TestTopicModel
from tests.utils.client import Client
from tests.utils.influx import create_point
from tests.utils.message import create_chat_completion_response, create_message


@pytest.fixture(autouse=True)
def mock_uuid4():
    counter = 0

    def side_effect() -> str:
        nonlocal counter
        counter += 1
        return f"pseudo-uuid-{counter}"

    with patch(
        "aidial_analytics_realtime.analytics.uuid4", side_effect=side_effect
    ):
        yield


@pytest.fixture
def influx():
    return InfluxWriterMock()


@pytest.fixture
def client(influx) -> Client:
    app.app.dependency_overrides[app.InfluxWriterAsync] = lambda: influx  # type: ignore
    app.app.dependency_overrides[app.TopicModel] = lambda: TestTopicModel()
    return Client(
        http_client=TestClient(app.app, raise_server_exceptions=False)
    )


def test_chat_completion_basic(client: Client, influx: InfluxWriterMock):
    message = create_message()
    client(message).raise_for_status()
    influx.match_points(create_point())


def test_chat_completion_chat_id(client: Client, influx: InfluxWriterMock):
    message = create_message(chat_id="test-chat-id")
    client(message).raise_for_status()
    influx.match_points(create_point(chat_id="test-chat-id"))


def test_chat_completion_project_id(client: Client, influx: InfluxWriterMock):
    message = create_message(project_id="test-project-id")
    client(message).raise_for_status()
    influx.match_points(create_point(project_id="test-project-id"))


def test_chat_completion_request_time(client: Client, influx: InfluxWriterMock):
    message = create_message(request_time="2023-11-24T03:33:40.39")
    client(message).raise_for_status()
    timestamp = parse_time(message["request"]["time"])
    influx.match_points(create_point(timestamp=timestamp))


def test_chat_completion_response_id_from_assembled_response(
    client: Client, influx: InfluxWriterMock
):
    response_assembled = create_chat_completion_response(id="test-response-id")
    message = create_message(response_assembled=response_assembled)
    client(message).raise_for_status()
    influx.match_points(create_point(response_id="test-response-id"))


def test_chat_completion_many_messages(
    client: Client, influx: InfluxWriterMock
):
    n = 50
    messages = [create_message(chat_id=f"chat-{idx}") for idx in range(0, n)]
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
    message = create_message(token_usage=None, response_assembled=response)
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

    message = create_message(
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

    message = create_message()
    message["request"]["body"] = json.dumps(
        {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": "act as a helpful assistant"}
                    ],
                },
                {"role": "user", "content": "ping?"},
            ],
        }
    )

    client(message).raise_for_status()

    point = create_point(topic="act as a helpful assistant\n\nping?\n\npong")
    influx.match_points(point)


def test_chat_completion_messages_without_text_content(
    client: Client, influx: InfluxWriterMock
):
    """Check that analytics ignores content parts without textual content"""

    message = create_message()
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


def test_embeddings_plain_text(client: Client, influx: InfluxWriterMock):
    client(
        {
            "apiType": "DialOpenAI",
            "chat": {"id": "chat-1"},
            "project": {"id": "PROJECT-KEY"},
            "user": {"id": "", "title": ""},
            "deployment": "text-embedding-3-small",
            "token_usage": {
                "completion_tokens": 0,
                "prompt_tokens": 2,
                "total_tokens": 2,
                "deployment_price": 0.001,
                "price": 0.001,
            },
            "parent_deployment": "assistant",
            "trace": {
                "trace_id": "5dca3d6ed5d22b6ab574f27a6ab5ec14",
                "core_span_id": "9ade2b6fef0a716d",
                "core_parent_span_id": "20e7e64715abbe97",
            },
            "execution_path": [None, "b", "c"],
            "request": {
                "protocol": "HTTP/1.1",
                "method": "POST",
                "uri": "/openai/deployments/text-embedding-3-small/embeddings?api-version=2023-03-15-preview",
                "time": "2023-08-16T19:42:39.997",
                "body": json.dumps({"input": ["fish", "cat"]}),
            },
            "response": {
                "status": "200",
                "body": json.dumps(
                    {
                        "data": [
                            {
                                "embedding": [0.1, 0.2],
                                "index": 0,
                                "object": "embedding",
                            },
                            {
                                "embedding": [0.3, 0.4],
                                "index": 1,
                                "object": "embedding",
                            },
                        ],
                        "model": "text-embedding-3-small",
                        "object": "list",
                        "usage": {
                            "prompt_tokens": 43,
                            "total_tokens": 43,
                        },
                    }
                ),
            },
        }
    ).raise_for_status()

    assert len(influx.points) == 1
    assert re.match(
        r'analytics,core_parent_span_id=20e7e64715abbe97,core_span_id=9ade2b6fef0a716d,deployment=text-embedding-3-small,execution_path=undefined/b/c,language=undefined,model=text-embedding-3-small,parent_deployment=assistant,project_id=PROJECT-KEY,response_id=(.+?),title=undefined,topic=fish\\n\\ncat,trace_id=5dca3d6ed5d22b6ab574f27a6ab5ec14,upstream=undefined cached_prompt_tokens=0i,chat_id="chat-1",completion_tokens=0i,deployment_price=0.001,number_request_messages=2i,price=0.001,prompt_tokens=2i,user_hash="undefined" 1692214959997000000',
        influx.points[0],
    )


def test_embeddings_no_body(client: Client, influx: InfluxWriterMock):
    client(
        {
            "apiType": "DialOpenAI",
            "chat": {"id": "chat-1"},
            "project": {"id": "PROJECT-KEY"},
            "user": {"id": "", "title": ""},
            "deployment": "text-embedding-3-small",
            "token_usage": {
                "completion_tokens": 0,
                "prompt_tokens": 2,
                "total_tokens": 2,
                "deployment_price": 0.001,
                "price": 0.001,
            },
            "parent_deployment": "assistant",
            "trace": {
                "trace_id": "5dca3d6ed5d22b6ab574f27a6ab5ec14",
                "core_span_id": "9ade2b6fef0a716d",
                "core_parent_span_id": "20e7e64715abbe97",
            },
            "execution_path": [None, "b", "c"],
            "request": {
                "protocol": "HTTP/1.1",
                "method": "POST",
                "uri": "/openai/deployments/text-embedding-3-small/embeddings?api-version=2023-03-15-preview",
                "time": "2023-08-16T19:42:39.997",
            },
            "response": {"status": "200"},
        }
    ).raise_for_status()

    assert len(influx.points) == 1
    assert re.match(
        r'analytics,core_parent_span_id=20e7e64715abbe97,core_span_id=9ade2b6fef0a716d,deployment=text-embedding-3-small,execution_path=undefined/b/c,language=undefined,model=text-embedding-3-small,parent_deployment=assistant,project_id=PROJECT-KEY,response_id=(.+?),title=undefined,topic=undefined,trace_id=5dca3d6ed5d22b6ab574f27a6ab5ec14,upstream=undefined cached_prompt_tokens=0i,chat_id="chat-1",completion_tokens=0i,deployment_price=0.001,number_request_messages=0i,price=0.001,prompt_tokens=2i,user_hash="undefined" 1692214959997000000',
        influx.points[0],
    )


def test_embeddings_tokens(client: Client, influx: InfluxWriterMock):
    client(
        {
            "apiType": "DialOpenAI",
            "chat": {"id": "chat-1"},
            "project": {"id": "PROJECT-KEY"},
            "user": {"id": "", "title": ""},
            "deployment": "text-embedding-3-small",
            "token_usage": {
                "completion_tokens": 0,
                "prompt_tokens": 2,
                "total_tokens": 2,
                "deployment_price": 0.001,
                "price": 0.001,
            },
            "parent_deployment": "assistant",
            "trace": {
                "trace_id": "5dca3d6ed5d22b6ab574f27a6ab5ec14",
                "core_span_id": "9ade2b6fef0a716d",
                "core_parent_span_id": "20e7e64715abbe97",
            },
            "execution_path": [None, "b", "c"],
            "request": {
                "protocol": "HTTP/1.1",
                "method": "POST",
                "uri": "/openai/deployments/text-embedding-3-small/embeddings?api-version=2023-03-15-preview",
                "time": "2023-08-16T19:42:39.997",
                "body": json.dumps({"input": [[1, 3, 4, 5], [6, 7, 8, 9]]}),
            },
            "response": {
                "status": "200",
                "body": json.dumps(
                    {
                        "data": [
                            {
                                "embedding": [0.1, 0.2],
                                "index": 0,
                                "object": "embedding",
                            },
                            {
                                "embedding": [0.3, 0.4],
                                "index": 1,
                                "object": "embedding",
                            },
                        ],
                        "model": "text-embedding-3-small",
                        "object": "list",
                        "usage": {
                            "prompt_tokens": 43,
                            "total_tokens": 43,
                        },
                    }
                ),
            },
        }
    ).raise_for_status()

    assert len(influx.points) == 1
    assert re.match(
        r'analytics,core_parent_span_id=20e7e64715abbe97,core_span_id=9ade2b6fef0a716d,deployment=text-embedding-3-small,execution_path=undefined/b/c,language=undefined,model=text-embedding-3-small,parent_deployment=assistant,project_id=PROJECT-KEY,response_id=(.+?),title=undefined,topic=undefined,trace_id=5dca3d6ed5d22b6ab574f27a6ab5ec14,upstream=undefined cached_prompt_tokens=0i,chat_id="chat-1",completion_tokens=0i,deployment_price=0.001,number_request_messages=2i,price=0.001,prompt_tokens=2i,user_hash="undefined" 1692214959997000000',
        influx.points[0],
    )


def test_chat_completion_parent_deployment(
    client: Client, influx: InfluxWriterMock
):
    message = create_message(parent_deployment="test-parent-deployment")
    client(message).raise_for_status()
    influx.match_points(
        create_point(parent_deployment="test-parent-deployment")
    )


def test_chat_completion_trace(client: Client, influx: InfluxWriterMock):
    message = create_message(
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
    message = create_message(execution_path=path)
    client(message).raise_for_status()
    influx.match_points(create_point(execution_path=expected_path))


def test_chat_completion_price(client: Client, influx: InfluxWriterMock):
    message = create_message(token_usage={"price": 0.456})
    client(message).raise_for_status()
    influx.match_points(create_point(price=0.456))


def test_chat_completion_deployment_price_no_price(
    client: Client, influx: InfluxWriterMock
):
    message = create_message(token_usage={"deployment_price": 0.123})
    client(message).raise_for_status()
    influx.match_points(create_point(deployment_price=0.0))


def test_chat_completion_deployment_price_with_price(
    client: Client, influx: InfluxWriterMock
):
    message = create_message(
        token_usage={"deployment_price": 0.123, "price": 0.456}
    )
    client(message).raise_for_status()
    influx.match_points(create_point(deployment_price=0.123, price=0.456))


def test_rate_request(client: Client, influx: InfluxWriterMock):

    client(
        {
            "apiType": "DialOpenAI",
            "chat": {"id": "chat-1"},
            "project": {"id": "PROJECT-KEY"},
            "user": {"id": "", "title": ""},
            "deployment": "gpt-4",
            "request": {
                "protocol": "HTTP/1.1",
                "method": "POST",
                "uri": "/v1/gpt-4/rate",
                "time": "2023-08-16T19:42:39.997",
                "body": json.dumps(
                    {
                        "responseId": "response_123",
                        "rate": True,
                    }
                ),
            },
            "assembled_response": "",
            "response": {
                "status": "200",
                "body": "",
            },
        },
        {
            "apiType": "DialOpenAI",
            "chat": {"id": "chat-1"},
            "project": {"id": "PROJECT-KEY"},
            "user": {"id": "", "title": ""},
            "deployment": "gpt-4",
            "request": {
                "protocol": "HTTP/1.1",
                "method": "POST",
                "uri": "/v1/gpt-4/rate",
                "time": "2023-11-24T03:33:40.39",
                "body": json.dumps(
                    {
                        "responseId": "response_124",
                        "rate": False,
                    }
                ),
            },
            "response": {
                "status": "200",
                "body": "",
            },
        },
    ).raise_for_status()

    assert influx.points == [
        "rate_analytics,chat_id=chat-1,deployment=gpt-4,project_id=PROJECT-KEY,response_id=response_123,title=undefined,user_hash=undefined dislike_count=0i,like_count=1i 1692214959997000000",
        "rate_analytics,chat_id=chat-1,deployment=gpt-4,project_id=PROJECT-KEY,response_id=response_124,title=undefined,user_hash=undefined dislike_count=1i,like_count=0i 1700796820390000000",
    ]


@pytest.mark.parametrize("assembled_response", [None, "{}", "", "invalid JSON"])
def test_chat_completion_invalid_assembled_response(
    client: Client,
    influx: InfluxWriterMock,
    assembled_response: str | None,
):
    message = create_message(response_assembled=assembled_response)
    client(message).raise_for_status()

    point = create_point(
        # Since there is no response.id, the response_id is auto-generated
        response_id="pseudo-uuid-1",
        topic="ping?",
        prompt_tokens=0,
        completion_tokens=0,
        deployment_price=0.0,
        price=0.0,
    )
    influx.match_points(point)


def test_invalid_data_message(client: Client):
    response = client.post_json(
        [
            "invalid message",
            {"message": "invalid message JSON"},
            {"message": '["\n'},
        ],
    ).raise_for_status()

    assert response.json() == [
        {
            "status": "error",
            "error": "1 validation error for Message\n__root__\n  Message expected dict not str (type=type_error)",
            "reason": "invalid request message",
        },
        {
            "status": "error",
            "error": "Expecting value: line 1 column 1 (char 0)",
            "reason": "invalid JSON in request message",
        },
        {
            "status": "error",
            "error": "Unterminated string starting at: line 1 column 2 (char 1)",
            "reason": "invalid JSON in request message",
        },
    ]


def test_unescaped_control_char_in_message(
    client: Client, influx: InfluxWriterMock
):
    response = client(
        create_message(project_id="PROJECT-\nKEY")
    ).raise_for_status()
    assert response.json() == [{"status": "success"}]

    point = create_point(project_id="PROJECT-\nKEY")
    influx.match_points(point)


def test_invalid_data_request_json(client: Client):
    response = client.http_client.post(
        "/data",
        content="invalid json",
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "json_invalid",
                "loc": ["body", 0],
                "msg": "JSON decode error",
                "input": {},
                "ctx": {"error": "Expecting value"},
            }
        ]
    }


def test_invalid_data_request_type(client: Client):
    response = client.post_json({"foo": "bar"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "__root__"],
                "msg": "value is not a valid list",
                "type": "type_error.list",
            }
        ]
    }
