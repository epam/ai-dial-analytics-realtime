import json

from tests.mocks import InfluxWriterMock
from tests.utils.client import Client


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
    assert (
        'analytics,core_parent_span_id=20e7e64715abbe97,core_span_id=9ade2b6fef0a716d,deployment=text-embedding-3-small,execution_path=undefined/b/c,language=undefined,model=text-embedding-3-small,parent_deployment=assistant,project_id=PROJECT-KEY,response_id=pseudo-uuid-1,title=undefined,topic=fish\\n\\ncat,trace_id=5dca3d6ed5d22b6ab574f27a6ab5ec14,upstream=undefined cached_prompt_tokens=0i,chat_id="chat-1",completion_tokens=0i,deployment_price=0.001,number_request_messages=2i,price=0.001,prompt_tokens=2i,user_hash="undefined" 1692214959997000000'
        == influx.points[0]
    )


def test_embeddings_no_response_body(client: Client, influx: InfluxWriterMock):
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
    assert (
        'analytics,core_parent_span_id=20e7e64715abbe97,core_span_id=9ade2b6fef0a716d,deployment=text-embedding-3-small,execution_path=undefined/b/c,language=undefined,model=text-embedding-3-small,parent_deployment=assistant,project_id=PROJECT-KEY,response_id=pseudo-uuid-1,title=undefined,topic=undefined,trace_id=5dca3d6ed5d22b6ab574f27a6ab5ec14,upstream=undefined cached_prompt_tokens=0i,chat_id="chat-1",completion_tokens=0i,deployment_price=0.001,number_request_messages=0i,price=0.001,prompt_tokens=2i,user_hash="undefined" 1692214959997000000'
        == influx.points[0]
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
    assert (
        'analytics,core_parent_span_id=20e7e64715abbe97,core_span_id=9ade2b6fef0a716d,deployment=text-embedding-3-small,execution_path=undefined/b/c,language=undefined,model=text-embedding-3-small,parent_deployment=assistant,project_id=PROJECT-KEY,response_id=pseudo-uuid-1,title=undefined,topic=undefined,trace_id=5dca3d6ed5d22b6ab574f27a6ab5ec14,upstream=undefined cached_prompt_tokens=0i,chat_id="chat-1",completion_tokens=0i,deployment_price=0.001,number_request_messages=2i,price=0.001,prompt_tokens=2i,user_hash="undefined" 1692214959997000000'
        == influx.points[0]
    )
