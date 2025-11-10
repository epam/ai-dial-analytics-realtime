import json

from tests.utils.constants import (
    DEFAULT_CHAT_ID,
    DEFAULT_PROJECT_ID,
    DEFAULT_RESPONSE_TIME,
)


def create_chat_completion_request():
    return {
        "n": 1,
        "stream": True,
        "messages": [
            {"role": "system", "content": ""},
            {"role": "user", "content": "ping?"},
        ],
        "model": "gpt-4",
        "max_tokens": 2000,
        "temperature": 0.0,
    }


def create_chat_completion_response(
    *,
    id: str = "chatcmpl-1",
    created: int = 1692214960,
):
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
    chat_id: str = DEFAULT_CHAT_ID,
    project_id: str = DEFAULT_PROJECT_ID,
    request_uri: str = "/openai/deployments/gpt-4/chat/completions?api-version=2023-03-15-preview",
    token_usage: dict | None = None,
    request_time: str = DEFAULT_RESPONSE_TIME,
    request_body: dict = create_chat_completion_request(),
    response_assembled: str | dict | None = create_chat_completion_response(),
):
    assembled_response = response_assembled
    if isinstance(response_assembled, dict):
        assembled_response = json.dumps(response_assembled)

    return {
        "apiType": "DialOpenAI",
        "chat": {"id": chat_id},
        "project": {"id": project_id},
        "user": {"id": "", "title": ""},
        "deployment": "gpt-4",
        "token_usage": token_usage,
        "request": {
            "protocol": "HTTP/1.1",
            "method": "POST",
            "uri": request_uri,
            "time": request_time,
            "body": json.dumps(request_body),
        },
        "assembled_response": assembled_response,
        # response.body is never inspected by the analytics for chat completion requests,
        # therefore, no need to make it realistic.
        "response": {"status": "200", "body": "whatever"},
    }
