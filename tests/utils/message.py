import json


def create_chat_completion_request():
    return {
        "n": 1,
        "stream": True,
        "messages": [
            {"role": "system", "content": ""},
            {"role": "user", "content": "ping"},
        ],
        "model": "gpt-4",
        "max_tokens": 2000,
        "temperature": 0.0,
    }


def create_chat_completion_response(*, id: str, created: int):
    return {
        "id": id,
        "object": "chat.completion.chunk",
        "created": created,
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


def create_message(
    *,
    chat_id: str,
    project_id: str,
    request_uri: str,
    request_time: str,
    request_body: dict,
    response_assembled: dict,
    response_body: str,
):
    return {
        "apiType": "DialOpenAI",
        "chat": {"id": chat_id},
        "project": {"id": project_id},
        "user": {"id": "", "title": ""},
        "deployment": "gpt-4",
        "request": {
            "protocol": "HTTP/1.1",
            "method": "POST",
            "uri": request_uri,
            "time": request_time,
            "body": json.dumps(request_body),
        },
        "assembled_response": json.dumps(response_assembled),
        "response": {"status": "200", "body": response_body},
    }
