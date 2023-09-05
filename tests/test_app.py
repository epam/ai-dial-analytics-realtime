import json
from fastapi.testclient import TestClient
from dial_analytics.app import app


def test_epam10k():
    client = TestClient(app)
    response = client.post(
        "/data",
        json=[{
            "message" : json.dumps({
                'apiType': 'DialOpenAI',
                'chat': {'id': ''},
                'project': {'id': 'PROJECT-KEY'},
                'user': {'id': '', 'title': ''},
                'request': {
                    'protocol': 'HTTP/1.1',
                    'method': 'POST',
                    'uri': '/openai/deployments/gpt-4/chat/completions?api-version=2023-03-15-preview',
                    'time': '2023-08-16T19:42:39.997',
                    'body': json.dumps({
                        'messages': [
                            {'role': 'system', 'content': ''},
                            {'role': 'user', 'content': "Hi!"}
                        ],
                        'model': 'gpt-4',
                        'max_tokens': 2000,
                        'stream': True,
                        'n': 1,
                        'temperature': 0.0
                    })
                },
                'response': {
                    'status': '200',
                    'body': 'data: {"id":"chatcmpl-7oGhcflZWv1vMpEoVDGPeAn87aJfh","object":"chat.completion.chunk","created":1692214960,"model":"gpt-4","choices":[{"index":0,"delta":{"role":"assistant","content":"Hi"},"finish_reason":null}]}\n\ndata: {"id":"chatcmpl-7oGhcflZWv1vMpEoVDGPeAn87aJfh","object":"chat.completion.chunk","created":1692214960,"model":"gpt-4","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"completion_tokens":189,"prompt_tokens":22,"total_tokens":211}}\n\ndata: [DONE]\n'
                }
            })
        }]
    )
    assert response.status_code == 200
