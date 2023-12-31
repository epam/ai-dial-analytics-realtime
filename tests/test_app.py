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
        'analytics,deployment=gpt-4,language=undefined,model=gpt-4,project_id=PROJECT-KEY,response_id=chatcmpl-1,title=undefined,topic=TestTopic,upstream=undefined chat_id="chat-1",completion_tokens=189i,number_request_messages=2i,price=0,prompt_tokens=22i,user_hash="undefined" 1692214959997000000',
        'analytics,deployment=gpt-4,language=undefined,model=gpt-4,project_id=PROJECT-KEY-2,response_id=chatcmpl-2,title=undefined,topic=TestTopic,upstream=undefined chat_id="chat-2",completion_tokens=189i,number_request_messages=2i,price=0,prompt_tokens=22i,user_hash="undefined" 1700796820390000000',
    ]
