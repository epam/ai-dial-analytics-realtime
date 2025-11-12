import json

import pytest
from fastapi.testclient import TestClient

import aidial_analytics_realtime.app as app
from tests.mocks import InfluxWriterMock, TestTopicModel
from tests.utils.client import Client


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
