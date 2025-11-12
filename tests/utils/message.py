import json
from typing import Callable

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


def _create_message(
    *,
    chat_id: str = DEFAULT_CHAT_ID,
    project_id: str = DEFAULT_PROJECT_ID,
    user_id: str = "test-user-id",
    user_title: str = "test-user-title",
    deployment: str = "gpt-4",
    request_uri: str = "/openai/deployments/gpt-4/chat/completions?api-version=2023-03-15-preview",
    token_usage: dict | None = _default_token_usage(),
    parent_deployment: str | None = "assistant",
    trace: dict | None = _default_trace(),
    execution_path: list | None = ["app1", "app2"],
    request_time: str = DEFAULT_RESPONSE_TIME,
    request_body: str | dict | None = create_chat_completion_request(),
    response_assembled: str | dict | None = create_chat_completion_response(),
    # response.body is never inspected by the analytics for chat completion requests,
    # therefore, no need to make it realistic.
    response_body: str | dict | None = "whatever",
    response_upstream_uri: str | None = "http://upstream.domain.com/endpoint",
) -> dict:
    assembled_response = response_assembled
    if isinstance(response_assembled, dict):
        assembled_response = json.dumps(response_assembled)

    if isinstance(response_body, dict):
        response_body = json.dumps(response_body)

    if isinstance(request_body, dict):
        request_body = json.dumps(request_body)

    return {
        "apiType": "DialOpenAI",
        "chat": {"id": chat_id},
        "project": {"id": project_id},
        "user": {"id": user_id, "title": user_title},
        "deployment": deployment,
        "token_usage": token_usage,
        "parent_deployment": parent_deployment,
        "trace": trace,
        "execution_path": execution_path,
        "request": {
            "protocol": "HTTP/1.1",
            "method": "POST",
            "uri": request_uri,
            "time": request_time,
            "body": request_body,
        },
        "assembled_response": assembled_response,
        "response": {
            "status": "200",
            "upstream_uri": response_upstream_uri,
            "body": response_body,
        },
    }


def create_chat_message(
    *,
    chat_id: str = DEFAULT_CHAT_ID,
    project_id: str = DEFAULT_PROJECT_ID,
    user_id: str = "test-user-id",
    user_title: str = "test-user-title",
    deployment: str = "gpt-4",
    request_uri: str = "/openai/deployments/gpt-4/chat/completions?api-version=2023-03-15-preview",
    token_usage: dict | None = _default_token_usage(),
    parent_deployment: str | None = "assistant",
    trace: dict | None = _default_trace(),
    execution_path: list | None = ["app1", "app2"],
    request_time: str = DEFAULT_RESPONSE_TIME,
    request_body: str | dict | None = create_chat_completion_request(),
    response_assembled: str | dict | None = create_chat_completion_response(),
    # response.body is never inspected by the analytics for chat completion requests,
    # therefore, no need to make it realistic.
    response_body: str | dict | None = "whatever",
    response_upstream_uri: str | None = "http://upstream.domain.com/endpoint",
) -> dict:
    return _create_message(**locals())


def _default_embedding_request_body() -> dict:
    return {"input": ["fish", "cat"]}


def _default_embedding_response_body() -> dict:
    return {
        "object": "list",
        "model": "text-embedding-3-small",
        "data": [
            {"index": 0, "object": "embedding", "embedding": [0.1, 0.2]},
            {"index": 1, "object": "embedding", "embedding": [0.3, 0.4]},
        ],
        "usage": {"prompt_tokens": 43, "total_tokens": 43},
    }


def create_embedding_message(
    *,
    chat_id: str = DEFAULT_CHAT_ID,
    project_id: str = DEFAULT_PROJECT_ID,
    user_id: str = "test-user-id",
    user_title: str = "test-user-title",
    deployment: str = "text-embedding-3-small",
    request_uri: str = "/openai/deployments/text-embedding-3-small/embeddings?api-version=2023-03-15-preview",
    token_usage: dict | None = _default_token_usage(),
    parent_deployment: str | None = "assistant",
    trace: dict | None = _default_trace(),
    execution_path: list | None = ["app1", "app2"],
    request_time: str = DEFAULT_RESPONSE_TIME,
    request_body: str | dict | None = _default_embedding_request_body(),
    response_assembled: str | dict | None = create_chat_completion_response(),
    response_body: str | dict | None = _default_embedding_response_body(),
    response_upstream_uri: str | None = "http://upstream.domain.com/endpoint",
) -> dict:
    return _create_message(**locals())


def _default_rate_request_body():
    return {"responseId": "rate-response-id", "rate": True}


def create_rate_message(
    *,
    chat_id: str = DEFAULT_CHAT_ID,
    project_id: str = DEFAULT_PROJECT_ID,
    user_id: str = "test-user-id",
    user_title: str = "test-user-title",
    deployment: str = "gpt-4",
    request_uri: str = "/v1/gpt-4/rate",
    token_usage: dict | None = None,
    parent_deployment: str | None = "assistant",
    trace: dict | None = _default_trace(),
    execution_path: list | None = ["app1", "app2"],
    request_time: str = DEFAULT_RESPONSE_TIME,
    request_body: str | dict | None = _default_rate_request_body(),
    response_assembled: str | dict | None = None,
    response_body: str | dict | None = "",
    response_upstream_uri: str | None = None,
) -> dict:
    return _create_message(**locals())


def on_request_body(message: dict, f: Callable[[dict], None | dict]) -> dict:
    body = json.loads(message["request"]["body"])
    body = f(body) or body
    message["request"]["body"] = json.dumps(body)
    return message
