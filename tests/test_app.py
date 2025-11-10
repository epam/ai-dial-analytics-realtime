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
from tests.utils.message import (
    create_chat_completion_request,
    create_chat_completion_response,
    create_message,
)


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


def test_chat_completion_plain_text_vanilla(
    client: Client, influx: InfluxWriterMock
):
    message1 = create_message()
    message2 = create_message(
        chat_id="chat-2",
        project_id="PROJECT-KEY-2",
        request_time="2023-11-24T03:33:40.39",
        request_body=create_chat_completion_request(),
        response_assembled=create_chat_completion_response(
            id="chatcmpl-2", created=1700828102
        ),
    )

    client(message1, message2).raise_for_status()

    point1 = create_point()
    point2 = create_point(
        project_id="PROJECT-KEY-2",
        response_id="chatcmpl-2",
        chat_id="chat-2",
        timestamp=parse_time(message2["request"]["time"]),
    )

    influx.match_points(point1, point2)


def test_chat_completion_plain_text_no_body(
    client: Client, influx: InfluxWriterMock
):
    # Checking that usage taken from message.token_usage when
    # it's not possible to extract it from the assembled response.

    message1 = create_message(
        chat_id="chat-1",
        token_usage={
            "prompt_tokens": 111,
            "completion_tokens": 222,
            "total_tokens": 333,
            "deployment_price": 0.001,
            "price": 0.002,
        },
        response_assembled=None,
    )

    message2 = create_message(
        chat_id="chat-2",
        token_usage={
            "prompt_tokens": 111,
            "completion_tokens": 222,
            "total_tokens": 333,
            "prompt_tokens_details": {"cached_tokens": 44},
            "deployment_price": 0.001,
            "price": 0.002,
        },
        response_assembled=None,
    )

    client(message1, message2).raise_for_status()

    point1 = create_point(
        chat_id="chat-1",
        response_id="pseudo-uuid-1",
        topic="ping?",
        price=0.002,
        deployment_price=0.001,
        prompt_tokens=111,
        completion_tokens=222,
    )

    point2 = create_point(
        chat_id="chat-2",
        response_id="pseudo-uuid-2",
        topic="ping?",
        price=0.002,
        deployment_price=0.001,
        cached_prompt_tokens=44,
        prompt_tokens=111,
        completion_tokens=222,
    )

    influx.match_points(point1, point2)


def test_chat_completion_list_content(client: Client, influx: InfluxWriterMock):
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


def test_chat_completion_none_content(client: Client, influx: InfluxWriterMock):
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


def test_data_request_with_new_format(client: Client, influx: InfluxWriterMock):

    client(
        {
            "apiType": "DialOpenAI",
            "chat": {"id": "chat-1"},
            "project": {"id": "PROJECT-KEY"},
            "user": {"id": "", "title": ""},
            "deployment": "gpt-4",
            "token_usage": {
                "completion_tokens": 40,
                "prompt_tokens": 30,
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
                "uri": "/openai/deployments/gpt-4/chat/completions?api-version=2023-03-15-preview",
                "time": "2023-08-16T19:42:39.997",
                "body": json.dumps(
                    {
                        "messages": [
                            {"role": "system", "content": ""},
                            {"role": "user", "content": "ping"},
                        ],
                        "model": "gpt-4",
                        "max_tokens": 2000,
                        "stream": True,
                        "n": 1,
                        "temperature": 0.0,
                    }
                ),
            },
            "assembled_response": json.dumps(
                {
                    "id": "chatcmpl-1",
                    "object": "chat.completion",
                    "created": 1692214960,
                    "model": "gpt-4",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "content": "pong",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "completion_tokens": 189,
                        "prompt_tokens": 22,
                        "total_tokens": 211,
                    },
                }
            ),
            "response": {
                "status": "200",
                "body": 'data: {"id":"chatcmpl-1","object":"chat.completion.chunk","created":1692214960,"model":"gpt-4","choices":[{"index":0,"delta":{"role":"assistant","content":"pong"},"finish_reason":null}]}\n\ndata: {"id":"chatcmpl-1","object":"chat.completion.chunk","created":1692214960,"model":"gpt-4","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"completion_tokens":189,"prompt_tokens":22,"total_tokens":211}}\n\ndata: [DONE]\n',
            },
        },
        {
            "apiType": "DialOpenAI",
            "chat": {"id": "chat-2"},
            "project": {"id": "PROJECT-KEY-2"},
            "user": {"id": "", "title": ""},
            "deployment": "gpt-4",
            "token_usage": {
                "completion_tokens": 40,
                "prompt_tokens": 30,
                "price": 0.005,
            },
            "trace": {
                "trace_id": "5dca3d6ed5d22b6ab574f27a6ab5ec14",
                "core_span_id": "20e7e64715abbe97",
            },
            "execution_path": ["a", "b", "c"],
            "request": {
                "protocol": "HTTP/1.1",
                "method": "POST",
                "uri": "/openai/deployments/gpt-4/chat/completions",
                "time": "2023-11-24T03:33:40.39",
                "body": json.dumps(
                    {
                        "messages": [
                            {"role": "system", "content": ""},
                            {"role": "user", "content": "ping"},
                        ],
                        "model": "gpt-4",
                        "max_tokens": 2000,
                        "stream": True,
                        "n": 1,
                        "temperature": 0.0,
                    }
                ),
            },
            "assembled_response": json.dumps(
                {
                    "id": "chatcmpl-2",
                    "object": "chat.completion",
                    "created": 1700828102,
                    "model": "gpt-4",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "content": "pong",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "completion_tokens": 189,
                        "prompt_tokens": 22,
                        "total_tokens": 211,
                    },
                }
            ),
            "response": {
                "status": "200",
                "body": 'data: {"id":"chatcmpl-2","object":"chat.completion.chunk","created":1700828102,"model":"gpt-4","choices":[{"index":0,"delta":{"role":"assistant","content":"pong"},"finish_reason":null}]}\n\ndata: {"id":"chatcmpl-2","object":"chat.completion.chunk","created":1700828102,"model":"gpt-4","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"completion_tokens":189,"prompt_tokens":22,"total_tokens":211}}\n\ndata: [DONE]\n',
            },
        },
    ).raise_for_status()

    assert influx.points == [
        'analytics,core_parent_span_id=20e7e64715abbe97,core_span_id=9ade2b6fef0a716d,deployment=gpt-4,execution_path=undefined/b/c,language=undefined,model=gpt-4,parent_deployment=assistant,project_id=PROJECT-KEY,response_id=chatcmpl-1,title=undefined,topic=ping\\n\\npong,trace_id=5dca3d6ed5d22b6ab574f27a6ab5ec14,upstream=undefined cached_prompt_tokens=0i,chat_id="chat-1",completion_tokens=40i,deployment_price=0.001,number_request_messages=2i,price=0.001,prompt_tokens=30i,user_hash="undefined" 1692214959997000000',
        'analytics,core_parent_span_id=undefined,core_span_id=20e7e64715abbe97,deployment=gpt-4,execution_path=a/b/c,language=undefined,model=gpt-4,parent_deployment=undefined,project_id=PROJECT-KEY-2,response_id=chatcmpl-2,title=undefined,topic=ping\\n\\npong,trace_id=5dca3d6ed5d22b6ab574f27a6ab5ec14,upstream=undefined cached_prompt_tokens=0i,chat_id="chat-2",completion_tokens=40i,deployment_price=0,number_request_messages=2i,price=0.005,prompt_tokens=30i,user_hash="undefined" 1700796820390000000',
    ]


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
                "uri": "/openai/deployments/gpt-4/chat/completions?api-version=2023-03-15-preview",
                "time": "2023-08-16T19:42:39.997",
                "body": json.dumps(
                    {
                        "messages": [
                            {"role": "system", "content": ""},
                            {"role": "user", "content": "ping"},
                        ],
                        "model": "gpt-4",
                        "max_tokens": 2000,
                        "stream": True,
                        "n": 1,
                        "temperature": 0.0,
                    }
                ),
            },
            "token_usage": {
                "completion_tokens": 189,
                "prompt_tokens": 22,
                "total_tokens": 211,
                "deployment_price": 0.001,
                "price": 0.001,
            },
            "assembled_response": assembled_response,
            "response": {
                "status": "200",
                "body": 'data: {"id":"chatcmpl-1","object":"chat.completion.chunk","created":1692214960,"model":"gpt-4","choices":[{"index":0,"delta":{"role":"assistant","content":"pong"},"finish_reason":null}]}\n\ndata: {"id":"chatcmpl-1","object":"chat.completion.chunk","created":1692214960,"model":"gpt-4","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"completion_tokens":189,"prompt_tokens":22,"total_tokens":211}}\n\ndata: [DONE]\n',
            },
        }
    ).raise_for_status()

    assert len(influx.points) == 1
    assert re.match(
        r'analytics,core_parent_span_id=undefined,core_span_id=undefined,deployment=gpt-4,execution_path=undefined,language=undefined,model=gpt-4,parent_deployment=undefined,project_id=PROJECT-KEY,response_id=(.+?),title=undefined,topic=ping,trace_id=undefined,upstream=undefined cached_prompt_tokens=0i,chat_id="chat-1",completion_tokens=189i,deployment_price=0.001,number_request_messages=2i,price=0.001,prompt_tokens=22i,user_hash="undefined" 1692214959997000000',
        influx.points[0],
    )


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
