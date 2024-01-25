import json
from unittest.mock import Mock

from fastapi.testclient import TestClient

import aidial_analytics_realtime.app as app
from tests.influx_writer_mock import InfluxWriterMock


def test_data_request():
    write_api_mock = InfluxWriterMock()
    app.app.dependency_overrides[app.InfluxWriterAsync] = lambda: write_api_mock

    topic_model = Mock()
    topic_model.get_topic.return_value = "TestTopic"
    app.app.dependency_overrides[app.TopicModel] = lambda: topic_model

    client = TestClient(app.app)
    response = client.post(
        "/data",
        json=[
            {
                "message": json.dumps(
                    {
                        "apiType": "DialOpenAI",
                        "chat": {"id": "chat-1"},
                        "project": {"id": "PROJECT-KEY"},
                        "user": {"id": "", "title": ""},
                        "request": {
                            "protocol": "HTTP/1.1",
                            "method": "POST",
                            "uri": "/openai/deployments/gpt-4/chat/completions?api-version=2023-03-15-preview",
                            "time": "2023-08-16T19:42:39.997",
                            "body": json.dumps(
                                {
                                    "messages": [
                                        {"role": "system", "content": ""},
                                        {"role": "user", "content": "Hi!"},
                                    ],
                                    "model": "gpt-4",
                                    "max_tokens": 2000,
                                    "stream": True,
                                    "n": 1,
                                    "temperature": 0.0,
                                }
                            ),
                        },
                        "response": {
                            "status": "200",
                            "body": 'data: {"id":"chatcmpl-1","object":"chat.completion.chunk","created":1692214960,"model":"gpt-4","choices":[{"index":0,"delta":{"role":"assistant","content":"Hi"},"finish_reason":null}]}\n\ndata: {"id":"chatcmpl-1","object":"chat.completion.chunk","created":1692214960,"model":"gpt-4","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"completion_tokens":189,"prompt_tokens":22,"total_tokens":211}}\n\ndata: [DONE]\n',
                        },
                    }
                )
            },
            {
                "message": json.dumps(
                    {
                        "apiType": "DialOpenAI",
                        "chat": {"id": "chat-2"},
                        "project": {"id": "PROJECT-KEY-2"},
                        "user": {"id": "", "title": ""},
                        "request": {
                            "protocol": "HTTP/1.1",
                            "method": "POST",
                            "uri": "/openai/deployments/gpt-4/chat/completions",
                            "time": "2023-11-24T03:33:40.39",
                            "body": json.dumps(
                                {
                                    "messages": [
                                        {"role": "system", "content": ""},
                                        {"role": "user", "content": "Hi!"},
                                    ],
                                    "model": "gpt-4",
                                    "max_tokens": 2000,
                                    "stream": True,
                                    "n": 1,
                                    "temperature": 0.0,
                                }
                            ),
                        },
                        "response": {
                            "status": "200",
                            "body": 'data: {"id":"chatcmpl-2","object":"chat.completion.chunk","created":1700828102,"model":"gpt-4","choices":[{"index":0,"delta":{"role":"assistant","content":"Hi"},"finish_reason":null}]}\n\ndata: {"id":"chatcmpl-2","object":"chat.completion.chunk","created":1700828102,"model":"gpt-4","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"completion_tokens":189,"prompt_tokens":22,"total_tokens":211}}\n\ndata: [DONE]\n',
                        },
                    }
                )
            },
        ],
    )
    assert response.status_code == 200
    assert write_api_mock.points == [
        'analytics,core_parent_span_id=undefined,core_span_id=undefined,deployment=gpt-4,execution_path=undefined,language=undefined,model=gpt-4,parent_deployment=undefined,project_id=PROJECT-KEY,response_id=chatcmpl-1,title=undefined,topic=TestTopic,trace_id=undefined,upstream=undefined chat_id="chat-1",completion_tokens=189i,deployment_price=0,number_request_messages=2i,price=0,prompt_tokens=22i,user_hash="undefined" 1692214959997000000',
        'analytics,core_parent_span_id=undefined,core_span_id=undefined,deployment=gpt-4,execution_path=undefined,language=undefined,model=gpt-4,parent_deployment=undefined,project_id=PROJECT-KEY-2,response_id=chatcmpl-2,title=undefined,topic=TestTopic,trace_id=undefined,upstream=undefined chat_id="chat-2",completion_tokens=189i,deployment_price=0,number_request_messages=2i,price=0,prompt_tokens=22i,user_hash="undefined" 1700796820390000000',
    ]


def test_data_request_with_new_format():
    write_api_mock = InfluxWriterMock()
    app.app.dependency_overrides[app.InfluxWriterAsync] = lambda: write_api_mock

    topic_model = Mock()
    topic_model.get_topic.return_value = "TestTopic"
    app.app.dependency_overrides[app.TopicModel] = lambda: topic_model

    client = TestClient(app.app)
    response = client.post(
        "/data",
        json=[
            {
                "message": json.dumps(
                    {
                        "apiType": "DialOpenAI",
                        "chat": {"id": "chat-1"},
                        "project": {"id": "PROJECT-KEY"},
                        "user": {"id": "", "title": ""},
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
                        "execution_path": "a->b->c",
                        "request": {
                            "protocol": "HTTP/1.1",
                            "method": "POST",
                            "uri": "/openai/deployments/gpt-4/chat/completions?api-version=2023-03-15-preview",
                            "time": "2023-08-16T19:42:39.997",
                            "body": json.dumps(
                                {
                                    "messages": [
                                        {"role": "system", "content": ""},
                                        {"role": "user", "content": "Hi!"},
                                    ],
                                    "model": "gpt-4",
                                    "max_tokens": 2000,
                                    "stream": True,
                                    "n": 1,
                                    "temperature": 0.0,
                                }
                            ),
                        },
                        "response": {
                            "status": "200",
                            "body": 'data: {"id":"chatcmpl-1","object":"chat.completion.chunk","created":1692214960,"model":"gpt-4","choices":[{"index":0,"delta":{"role":"assistant","content":"Hi"},"finish_reason":null}]}\n\ndata: {"id":"chatcmpl-1","object":"chat.completion.chunk","created":1692214960,"model":"gpt-4","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"completion_tokens":189,"prompt_tokens":22,"total_tokens":211}}\n\ndata: [DONE]\n',
                        },
                    }
                )
            },
            {
                "message": json.dumps(
                    {
                        "apiType": "DialOpenAI",
                        "chat": {"id": "chat-2"},
                        "project": {"id": "PROJECT-KEY-2"},
                        "user": {"id": "", "title": ""},
                        "token_usage": {
                            "completion_tokens": 40,
                            "prompt_tokens": 30,
                            "price": 0.005,
                        },
                        "trace": {
                            "trace_id": "5dca3d6ed5d22b6ab574f27a6ab5ec14",
                            "core_span_id": "20e7e64715abbe97",
                        },
                        "execution_path": "a->b->c",
                        "request": {
                            "protocol": "HTTP/1.1",
                            "method": "POST",
                            "uri": "/openai/deployments/gpt-4/chat/completions",
                            "time": "2023-11-24T03:33:40.39",
                            "body": json.dumps(
                                {
                                    "messages": [
                                        {"role": "system", "content": ""},
                                        {"role": "user", "content": "Hi!"},
                                    ],
                                    "model": "gpt-4",
                                    "max_tokens": 2000,
                                    "stream": True,
                                    "n": 1,
                                    "temperature": 0.0,
                                }
                            ),
                        },
                        "response": {
                            "status": "200",
                            "body": 'data: {"id":"chatcmpl-2","object":"chat.completion.chunk","created":1700828102,"model":"gpt-4","choices":[{"index":0,"delta":{"role":"assistant","content":"Hi"},"finish_reason":null}]}\n\ndata: {"id":"chatcmpl-2","object":"chat.completion.chunk","created":1700828102,"model":"gpt-4","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"completion_tokens":189,"prompt_tokens":22,"total_tokens":211}}\n\ndata: [DONE]\n',
                        },
                    }
                )
            },
        ],
    )
    assert response.status_code == 200
    assert write_api_mock.points == [
        'analytics,core_parent_span_id=20e7e64715abbe97,core_span_id=9ade2b6fef0a716d,deployment=gpt-4,execution_path=a->b->c,language=undefined,model=gpt-4,parent_deployment=assistant,project_id=PROJECT-KEY,response_id=chatcmpl-1,title=undefined,topic=TestTopic,trace_id=5dca3d6ed5d22b6ab574f27a6ab5ec14,upstream=undefined chat_id="chat-1",completion_tokens=40i,deployment_price=0.001,number_request_messages=2i,price=0.001,prompt_tokens=30i,user_hash="undefined" 1692214959997000000',
        'analytics,core_parent_span_id=undefined,core_span_id=20e7e64715abbe97,deployment=gpt-4,execution_path=a->b->c,language=undefined,model=gpt-4,parent_deployment=undefined,project_id=PROJECT-KEY-2,response_id=chatcmpl-2,title=undefined,topic=TestTopic,trace_id=5dca3d6ed5d22b6ab574f27a6ab5ec14,upstream=undefined chat_id="chat-2",completion_tokens=40i,deployment_price=0,number_request_messages=2i,price=0.005,prompt_tokens=30i,user_hash="undefined" 1700796820390000000',
    ]
