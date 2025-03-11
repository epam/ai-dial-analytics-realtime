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
    project_id: str = DEFAULT_PROJECT_ID,
    response_id: str = DEFAULT_RESPONSE_ID,
    chat_id: str = DEFAULT_CHAT_ID,
    topic: str | None = DEFAULT_TOPIC,
    title: str = DEFAULT_TITLE,
    timestamp: datetime = DEFAULT_TIMESTAMP,
    price: float = 0.0,
    deployment_price: float = 0.0,
    completion_tokens: int = 189,
    prompt_tokens: int = 22,
) -> Point:
    return (
        Point("analytics")
        .tag("model", "gpt-4")
        .tag("deployment", "gpt-4")
        .tag("parent_deployment", "undefined")
        .tag("execution_path", "undefined")
        .tag("trace_id", "undefined")
        .tag("core_span_id", "undefined")
        .tag("core_parent_span_id", "undefined")
        .tag("project_id", project_id)
        .tag("language", "undefined")
        .tag("upstream", "undefined")
        .tag("topic", topic)
        .tag("title", title)
        .tag("response_id", response_id)
        .field("user_hash", "undefined")
        .field("price", price)
        .field("deployment_price", deployment_price)
        .field("number_request_messages", 2)
        .field("chat_id", chat_id)
        .field("completion_tokens", completion_tokens)
        .field("prompt_tokens", prompt_tokens)
        .time(timestamp)
    )
