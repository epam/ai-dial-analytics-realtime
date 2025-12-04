from datetime import datetime

from influxdb_client import Point

from tests.utils.constants import (
    DEFAULT_CHAT_ID,
    DEFAULT_PROJECT_ID,
    DEFAULT_RESPONSE_ID,
    DEFAULT_TIMESTAMP,
    DEFAULT_USER_ID,
    DEFAULT_USER_TITLE,
)


def create_rate_point(
    *,
    deployment: str = "gpt-4",
    project_id: str = DEFAULT_PROJECT_ID,
    response_id: str = DEFAULT_RESPONSE_ID,
    chat_id: str | None = DEFAULT_CHAT_ID,
    user_hash: str | None = DEFAULT_USER_ID,
    title: str | None = DEFAULT_USER_TITLE,
    timestamp: datetime = DEFAULT_TIMESTAMP,
    like_count: int = 1,
    dislike_count: int = 0,
):
    return (
        Point("rate_analytics")
        .tag("deployment", deployment)
        .tag("project_id", project_id)
        .tag("title", title or "undefined")
        .tag("response_id", response_id)
        .tag("user_hash", user_hash or "undefined")
        .tag("chat_id", chat_id or "undefined")
        .field("dislike_count", dislike_count)
        .field("like_count", like_count)
        .time(timestamp)
    )


def create_point(
    *,
    parent_deployment: str | None = "assistant",
    execution_path: str | None = "app1/app2",
    model: str = "gpt-4",
    deployment: str = "gpt-4",
    trace_id: str | None = "default_trace_id",
    core_span_id: str | None = "default_core_span_id",
    core_parent_span_id: str | None = "default_core_parent_span_id",
    project_id: str = DEFAULT_PROJECT_ID,
    language: str | None = None,
    response_id: str = DEFAULT_RESPONSE_ID,
    user_hash: str | None = DEFAULT_USER_ID,
    chat_id: str = DEFAULT_CHAT_ID,
    number_request_messages: int = 1,
    upstream: str | None = "http://upstream.domain.com/endpoint",
    topic: str | None = None,
    title: str | None = DEFAULT_USER_TITLE,
    timestamp: datetime = DEFAULT_TIMESTAMP,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cached_prompt_tokens: int = 0,
    deployment_price: float = 0.0,
    price: float = 0.0,
) -> Point:
    return (
        Point("analytics")
        .tag("model", model)
        .tag("deployment", deployment)
        .tag("parent_deployment", parent_deployment or "undefined")
        .tag("execution_path", execution_path or "undefined")
        .tag("trace_id", trace_id or "undefined")
        .tag("core_span_id", core_span_id or "undefined")
        .tag("core_parent_span_id", core_parent_span_id or "undefined")
        .tag("project_id", project_id)
        .tag("language", language or "undefined")
        .tag("upstream", upstream or "undefined")
        .tag("topic", topic or "undefined")
        .tag("title", title or "undefined")
        .tag("response_id", response_id)
        .field("user_hash", user_hash or "undefined")
        .field("price", price)
        .field("deployment_price", deployment_price)
        .field("number_request_messages", number_request_messages)
        .field("chat_id", chat_id)
        .field("completion_tokens", completion_tokens)
        .field("prompt_tokens", prompt_tokens)
        .field("cached_prompt_tokens", cached_prompt_tokens)
        .time(timestamp)
    )
