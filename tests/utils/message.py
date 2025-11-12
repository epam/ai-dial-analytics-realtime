import json

from tests.utils.constants import (
    DEFAULT_CHAT_ID,
    DEFAULT_PROJECT_ID,
    DEFAULT_RESPONSE_TIME,
)


def create_chat_completion_request():
    return {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": ""},
            {"role": "user", "content": "ping?"},
        ],
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
            "prompt_tokens_details": {"cached_tokens": 10},
        },
    }


def _default_token_usage() -> dict:
    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "prompt_tokens_details": {"cached_tokens": 0},
        "deployment_price": 0.0,
        "price": 0.0,
    }


def _default_trace() -> dict:
    return {
        "trace_id": "test-trace-id",
        "core_span_id": "test-core-span-id",
        "core_parent_span_id": "core-parent-span-id",
    }


def create_message(
    *,
    chat_id: str = DEFAULT_CHAT_ID,
    project_id: str = DEFAULT_PROJECT_ID,
    user_id: str = "test-user-id",
    user_title: str = "test-user-title",
    request_uri: str = "/openai/deployments/gpt-4/chat/completions?api-version=2023-03-15-preview",
    token_usage: dict | None = _default_token_usage(),
    parent_deployment: str | None = "assistant",
    trace: dict | None = _default_trace(),
    execution_path: list | None = ["app1", "app2"],
    request_time: str = DEFAULT_RESPONSE_TIME,
    request_body: dict = create_chat_completion_request(),
    response_assembled: str | dict | None = create_chat_completion_response(),
    response_upstream_uri: str | None = "http://upstream.domain.com/endpoint",
):
    assembled_response = response_assembled
    if isinstance(response_assembled, dict):
        assembled_response = json.dumps(response_assembled)

    return {
        "apiType": "DialOpenAI",
        "chat": {"id": chat_id},
        "project": {"id": project_id},
        "user": {"id": user_id, "title": user_title},
        "deployment": "gpt-4",
        "token_usage": token_usage,
        "parent_deployment": parent_deployment,
        "trace": trace,
        "execution_path": execution_path,
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
        "response": {
            "status": "200",
            "upstream_uri": response_upstream_uri,
            "body": "whatever",
        },
    }
