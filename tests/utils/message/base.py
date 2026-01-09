import json
from typing import Callable

from tests.utils.constants import (
    DEFAULT_CORE_PARENT_SPAN_ID,
    DEFAULT_CORE_SPAN_ID,
    DEFAULT_TRACE_ID,
)


def default_token_usage() -> dict:
    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "prompt_tokens_details": {"cached_tokens": 0},
        "deployment_price": 0.0,
        "price": 0.0,
    }


def default_trace() -> dict:
    return {
        "trace_id": DEFAULT_TRACE_ID,
        "core_span_id": DEFAULT_CORE_SPAN_ID,
        "core_parent_span_id": DEFAULT_CORE_PARENT_SPAN_ID,
    }


def create_message(
    *,
    chat_id: str,
    project_id: str,
    user_id: str,
    user_title: str,
    deployment: str,
    request_uri: str,
    token_usage: dict | None,
    parent_deployment: str | None,
    trace: dict | None,
    execution_path: list | None,
    request_time: str,
    request_body: str | dict | None,
    response_assembled: str | dict | None,
    response_body: str | dict | None,
    response_upstream_uri: str | None,
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


def on_request_body(message: dict, f: Callable[[dict], None | dict]) -> dict:
    body = json.loads(message["request"]["body"])
    body = f(body) or body
    message["request"]["body"] = json.dumps(body)
    return message
