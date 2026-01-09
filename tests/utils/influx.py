from datetime import datetime

from influxdb_client import Point

from tests.utils.constants import (
    DEFAULT_CHAT_ID,
    DEFAULT_CORE_PARENT_SPAN_ID,
    DEFAULT_CORE_SPAN_ID,
    DEFAULT_DEPLOYMENT,
    DEFAULT_EXECUTION_PATH_STR,
    DEFAULT_MODEL,
    DEFAULT_PARENT_DEPLOYMENT,
    DEFAULT_PROJECT_ID,
    DEFAULT_RESPONSE_ID,
    DEFAULT_TIMESTAMP,
    DEFAULT_TRACE_ID,
    DEFAULT_UPSTREAM_URI,
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


def _create_point(
    *,
    parent_deployment: str | None,
    execution_path: str | None,
    model: str,
    deployment: str,
    trace_id: str | None,
    core_span_id: str | None,
    core_parent_span_id: str | None,
    project_id: str,
    language: str | None,
    response_id: str,
    user_hash: str | None,
    chat_id: str,
    number_request_messages: int,
    upstream: str | None,
    topic: str | None,
    title: str | None,
    timestamp: datetime,
    prompt_tokens: int,
    completion_tokens: int,
    cached_prompt_tokens: int,
    deployment_price: float,
    price: float,
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


def create_chat_point(
    *,
    parent_deployment: str | None = DEFAULT_PARENT_DEPLOYMENT,
    execution_path: str | None = DEFAULT_EXECUTION_PATH_STR,
    model: str = DEFAULT_MODEL,
    deployment: str = DEFAULT_DEPLOYMENT,
    trace_id: str | None = DEFAULT_TRACE_ID,
    core_span_id: str | None = DEFAULT_CORE_SPAN_ID,
    core_parent_span_id: str | None = DEFAULT_CORE_PARENT_SPAN_ID,
    project_id: str = DEFAULT_PROJECT_ID,
    language: str | None = None,
    response_id: str = DEFAULT_RESPONSE_ID,
    user_hash: str | None = DEFAULT_USER_ID,
    chat_id: str = DEFAULT_CHAT_ID,
    number_request_messages: int = 1,
    upstream: str | None = DEFAULT_UPSTREAM_URI,
    topic: str | None = None,
    title: str | None = DEFAULT_USER_TITLE,
    timestamp: datetime = DEFAULT_TIMESTAMP,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cached_prompt_tokens: int = 0,
    deployment_price: float = 0.0,
    price: float = 0.0,
) -> Point:
    return _create_point(**locals())


def create_embeddings_point(
    *,
    parent_deployment: str | None = DEFAULT_PARENT_DEPLOYMENT,
    execution_path: str | None = DEFAULT_EXECUTION_PATH_STR,
    deployment: str = DEFAULT_DEPLOYMENT,
    trace_id: str | None = DEFAULT_TRACE_ID,
    core_span_id: str | None = DEFAULT_CORE_SPAN_ID,
    core_parent_span_id: str | None = DEFAULT_CORE_PARENT_SPAN_ID,
    project_id: str = DEFAULT_PROJECT_ID,
    language: str | None = None,
    response_id: str = DEFAULT_RESPONSE_ID,
    user_hash: str | None = DEFAULT_USER_ID,
    chat_id: str = DEFAULT_CHAT_ID,
    number_request_messages: int = 1,
    upstream: str | None = DEFAULT_UPSTREAM_URI,
    topic: str | None = None,
    title: str | None = DEFAULT_USER_TITLE,
    timestamp: datetime = DEFAULT_TIMESTAMP,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cached_prompt_tokens: int = 0,
    deployment_price: float = 0.0,
    price: float = 0.0,
) -> Point:
    model = deployment  # type: ignore
    return _create_point(**locals())
