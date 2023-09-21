import json
import os
from unittest import mock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def mock_settings_env_vars():
    with mock.patch.dict(
        os.environ,
        {
            "INFLUX_URL": "influx_url",
            "INFLUX_ORG": "influx_org",
            "INFLUX_BUCKET": "influx_bucket",
        },
    ):
        yield


class InfluxWriteApiMock:
    def __init__(self):
        self.points = []

    async def write(self, bucket, record):
        assert bucket == "influx_bucket"
        self.points.append(str(record))


@mock.patch("influxdb_client.client.influxdb_client_async.InfluxDBClientAsync")
def test_data_request(influxdb_client_async):
    import ai_dial_analytics_realtime.app

    write_api_mock = InfluxWriteApiMock()
    ai_dial_analytics_realtime.app.influx_write_api = write_api_mock

    client = TestClient(ai_dial_analytics_realtime.app.app)
    response = client.post(
        "/data",
        json=[
            {
                "message": json.dumps(
                    {
                        "apiType": "DialOpenAI",
                        "chat": {"id": ""},
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
            }
        ],
    )
    assert response.status_code == 200
    assert write_api_mock.points == [
        'analytics,deployment=gpt-4,language=undefined,model=gpt-4,project_id=PROJECT-KEY,response_id=chatcmpl-1,title=undefined,upstream=undefined chat_id="undefined",completion_tokens=189i,number_request_messages=2i,price=0,prompt_tokens=22i,user_hash="undefined" 1692207759997000000'
    ]
