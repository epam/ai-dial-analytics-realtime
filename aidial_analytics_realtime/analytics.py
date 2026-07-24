from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import assert_never
from uuid import uuid4

from influxdb_client import Point

from aidial_analytics_realtime.dial import (
    get_chat_completion_request_contents,
    get_chat_completion_response_contents,
    get_embeddings_request_contents,
)
from aidial_analytics_realtime.influx_writer import InfluxWriterAsync
from aidial_analytics_realtime.langid import LangID
from aidial_analytics_realtime.topic_model import TopicModel


class RequestType(Enum):
    CHAT_COMPLETION = 1
    EMBEDDING = 2


async def detect_lang(
    lang_id: LangID,
    request: dict,
    response: dict,
    request_type: RequestType,
) -> str:
    match request_type:
        case RequestType.CHAT_COMPLETION:
            request_contents = get_chat_completion_request_contents(request)
            response_content = get_chat_completion_response_contents(response)
            text = "\n\n".join(request_contents[-1:] + response_content)
        case RequestType.EMBEDDING:
            text = "\n\n".join(get_embeddings_request_contents(request))
        case _:
            assert_never(request_type)

    return to_string(await lang_id.detect_language(text))


def to_string(obj: str | None) -> str:
    return obj or "undefined"


def build_execution_path(path: list | None):
    if not path:
        return "undefined"
    return "/".join(to_string(segment).replace("/", "\\/") for segment in path)


async def make_point(
    deployment: str,
    model: str,
    project_id: str,
    chat_id: str | None,
    upstream_url: str | None,
    user_hash: str,
    user_title: str,
    timestamp: datetime,
    request: dict | None,
    response: dict | None,
    request_type: RequestType,
    usage: dict | None,
    topic_model: TopicModel,
    lang_id: LangID,
    parent_deployment: str | None,
    trace: dict | None,
    execution_path: list | None,
):
    topic = None

    if chat_id:
        match request_type:
            case RequestType.CHAT_COMPLETION:
                response_contents = get_chat_completion_response_contents(
                    response
                )
                request_contents = get_chat_completion_request_contents(request)

                topic = to_string(
                    await topic_model.get_topic_by_text(
                        "\n\n".join(request_contents + response_contents),
                    )
                )
            case RequestType.EMBEDDING:
                request_contents = get_embeddings_request_contents(request)

                topic = to_string(
                    await topic_model.get_topic_by_text(
                        "\n\n".join(request_contents)
                    )
                )
            case _:
                assert_never(request_type)

    price = Decimal(0)
    deployment_price = Decimal(0)
    if usage is not None and usage.get("price") is not None:
        price = usage["price"]
        deployment_price = usage.get("deployment_price", Decimal(0))

    point = (
        Point("analytics")
        .tag("model", model)
        .tag("deployment", deployment)
        .tag("parent_deployment", to_string(parent_deployment))
        .tag(
            "execution_path",
            build_execution_path(execution_path),
        )
        .tag("trace_id", "undefined" if not trace else trace["trace_id"])
        .tag(
            "core_span_id", "undefined" if not trace else trace["core_span_id"]
        )
        .tag(
            "core_parent_span_id",
            (
                "undefined"
                if not trace
                else to_string(trace.get("core_parent_span_id"))
            ),
        )
        .tag("project_id", project_id)
        .tag(
            "language",
            (
                "undefined"
                if not chat_id or request is None or response is None
                else await detect_lang(lang_id, request, response, request_type)
            ),
        )
        .tag("upstream", to_string(upstream_url))
        .tag("topic", topic)
        .tag("title", to_string(user_title))
        .tag(
            "response_id",
            (
                response["id"]
                if request_type == RequestType.CHAT_COMPLETION
                and response is not None
                and "id" in response
                else uuid4()
            ),
        )
        .field("user_hash", to_string(user_hash))
        .field("price", float(price))
        .field("deployment_price", float(deployment_price))
        .field(
            "number_request_messages",
            (
                0
                if request is None
                else (
                    len(request["messages"])
                    if request_type == RequestType.CHAT_COMPLETION
                    else (
                        1
                        if isinstance(request["input"], str)
                        else len(request["input"])
                    )
                )
            ),
        )
        .field("chat_id", to_string(chat_id))
        .time(timestamp)
    )

    usage = usage or {}
    point.field("completion_tokens", usage.get("completion_tokens") or 0)
    point.field("prompt_tokens", usage.get("prompt_tokens") or 0)

    details = usage.get("prompt_tokens_details") or {}
    point.field("cached_prompt_tokens", details.get("cached_tokens") or 0)

    return point


def make_mcp_point(
    *,
    deployment: str,
    parent_deployment: str | None,
    project_id: str,
    chat_id: str | None,
    upstream_url: str | None,
    user_hash: str,
    user_title: str,
    timestamp: datetime,
    request: dict | None,
    trace: dict | None,
    execution_path: list | None,
):
    trace = trace or {}
    request = request or {}

    mcp_method = request.get("method")

    mcp_tool_call_name = None
    if mcp_method == "tools/call" and (params := request.get("params")):
        mcp_tool_call_name = params.get("name")

    return (
        Point("mcp_analytics")
        .tag("project_id", project_id)
        .tag("title", to_string(user_title))
        .tag("deployment", deployment)
        .tag("parent_deployment", to_string(parent_deployment))
        .tag("mcp_method", to_string(mcp_method))
        .field("execution_path", build_execution_path(execution_path))
        .field("trace_id", to_string(trace.get("trace_id")))
        .field("core_span_id", to_string(trace.get("core_span_id")))
        .field(
            "core_parent_span_id", to_string(trace.get("core_parent_span_id"))
        )
        .field("upstream", to_string(upstream_url))
        .field("user_hash", to_string(user_hash))
        .field("chat_id", to_string(chat_id))
        .field("mcp_tool_call_name", to_string(mcp_tool_call_name))
        .time(timestamp)
    )


def make_route_point(
    *,
    deployment: str,
    route_path: str,
    http_method: str,
    parent_deployment: str | None,
    project_id: str,
    chat_id: str | None,
    upstream_url: str | None,
    user_hash: str,
    user_title: str,
    timestamp: datetime,
    trace: dict | None,
    execution_path: list | None,
):
    trace = trace or {}

    return (
        Point("routes_analytics")
        .tag("project_id", project_id)
        .tag("title", to_string(user_title))
        .tag("deployment", deployment)
        .tag("route_path", route_path)
        .tag("http_method", http_method)
        .tag("parent_deployment", to_string(parent_deployment))
        .field("execution_path", build_execution_path(execution_path))
        .field("trace_id", to_string(trace.get("trace_id")))
        .field("core_span_id", to_string(trace.get("core_span_id")))
        .field(
            "core_parent_span_id", to_string(trace.get("core_parent_span_id"))
        )
        .field("upstream", to_string(upstream_url))
        .field("user_hash", to_string(user_hash))
        .field("chat_id", to_string(chat_id))
        .time(timestamp)
    )


def make_rate_point(
    deployment: str,
    project_id: str,
    chat_id: str | None,
    user_hash: str,
    user_title: str,
    timestamp: datetime,
    request_body: dict,
):
    like = request_body["rate"]
    like_count = 1 if like else 0
    dislike_count = 1 if not like else 0
    point = (
        Point("rate_analytics")
        .tag("deployment", deployment)
        .tag("project_id", project_id)
        .tag("title", to_string(user_title))
        .tag("response_id", request_body["responseId"])
        .tag("user_hash", to_string(user_hash))
        .tag("chat_id", to_string(chat_id))
        .field("dislike_count", dislike_count)
        .field("like_count", like_count)
        .time(timestamp)
    )
    return point


async def on_message(
    influx_writer: InfluxWriterAsync,
    deployment: str,
    model: str,
    project_id: str,
    chat_id: str,
    upstream_url: str,
    user_hash: str,
    user_title: str,
    timestamp: datetime,
    request: dict | None,
    response: dict | None,
    type: RequestType,
    topic_model: TopicModel,
    lang_id: LangID,
    token_usage: dict | None,
    parent_deployment: str | None,
    trace: dict | None,
    execution_path: list | None,
):
    response_usage = None if response is None else response.get("usage")

    point = await make_point(
        deployment,
        model,
        project_id,
        chat_id,
        upstream_url,
        user_hash,
        user_title,
        timestamp,
        request,
        response,
        type,
        token_usage or response_usage,
        topic_model,
        lang_id,
        parent_deployment,
        trace,
        execution_path,
    )
    await influx_writer(point)
