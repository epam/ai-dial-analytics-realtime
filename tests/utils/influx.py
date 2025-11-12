from datetime import datetime

from influxdb_client import Point

from tests.utils.constants import (
    DEFAULT_CHAT_ID,
    DEFAULT_PROJECT_ID,
    DEFAULT_RESPONSE_ID,
    DEFAULT_TIMESTAMP,
    DEFAULT_TITLE,
    DEFAULT_TOPIC,
)


def create_point(
    *,
    parent_deployment: str | None = None,
    execution_path: str | None = None,
    trace_id: str | None = None,
    core_span_id: str | None = None,
    core_parent_span_id: str | None = None,
    project_id: str = DEFAULT_PROJECT_ID,
    response_id: str = DEFAULT_RESPONSE_ID,
    chat_id: str = DEFAULT_CHAT_ID,
    number_request_messages: int = 2,
    topic: str | None = DEFAULT_TOPIC,
    title: str = DEFAULT_TITLE,
    timestamp: datetime = DEFAULT_TIMESTAMP,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cached_prompt_tokens: int = 0,
    deployment_price: float = 0.0,
    price: float = 0.0,
) -> Point:
    return (
        Point("analytics")
        .tag("model", "gpt-4")
        .tag("deployment", "gpt-4")
        .tag("parent_deployment", parent_deployment or "undefined")
        .tag("execution_path", execution_path or "undefined")
        .tag("trace_id", trace_id or "undefined")
        .tag("core_span_id", core_span_id or "undefined")
        .tag("core_parent_span_id", core_parent_span_id or "undefined")
        .tag("project_id", project_id)
        .tag("language", "undefined")
        .tag("upstream", "undefined")
        .tag("topic", topic)
        .tag("title", title)
        .tag("response_id", response_id)
        .field("user_hash", "undefined")
        .field("price", price)
        .field("deployment_price", deployment_price)
        .field("number_request_messages", number_request_messages)
        .field("chat_id", chat_id)
        .field("completion_tokens", completion_tokens)
        .field("prompt_tokens", prompt_tokens)
        .field("cached_prompt_tokens", cached_prompt_tokens)
        .time(timestamp)
    )
