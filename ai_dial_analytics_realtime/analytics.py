import os
from datetime import timedelta
from enum import Enum
from logging import Logger
from uuid import uuid4

from influxdb_client import Point
from influxdb_client.client.write_api_async import WriteApiAsync
from langid.langid import LanguageIdentifier, model

import ai_dial_analytics_realtime.rates as rates
from ai_dial_analytics_realtime.topic_model import get_topic, get_topic_by_text

identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)


class RequestType(Enum):
    CHAT_COMPLETION = 1
    EMBEDDING = 2


def detect_lang(request, response, request_type):
    if request_type == RequestType.CHAT_COMPLETION:
        text = (
            request["messages"][-1]["content"]
            + "\n\n"
            + response["choices"][0]["message"]["content"]
        )
    else:
        text = (
            request["input"]
            if request["input"] is str
            else "\n\n".join(request["input"])
        )

    return detect_lang_by_text(text)


def detect_lang_by_text(text):
    try:
        lang, prob = identifier.classify(text)

        if prob > 0.998:
            return lang

        return "undefined"
    except Exception:
        return "undefined"


influx_bucket = os.environ["INFLUX_BUCKET"]


def to_string(obj: str | None):
    return obj if obj else "undefined"


def make_point(
    deployment: str,
    model: str,
    project_id: str,
    chat_id: str | None,
    upstream_url: str | None,
    user_hash: str,
    user_title: str,
    timestamp_ms: int,
    request: dict,
    response: dict,
    request_type: RequestType,
    usage: dict | None,
):
    topic = None
    response_content = ""
    request_content = ""
    if request_type == RequestType.CHAT_COMPLETION:
        response_content = response["choices"][0]["message"]["content"]
        request_content = "\n".join(
            [message["content"] for message in request["messages"]]
        )
        if chat_id:
            topic = get_topic(request["messages"], response_content)
    else:
        request_content = (
            request["input"]
            if request["input"] is str
            else "\n".join(request["input"])
        )
        if chat_id:
            topic = get_topic_by_text(
                request["input"]
                if request["input"] is str
                else "\n\n".join(request["input"])
            )

    price = rates.calculate_price(
        model, request_content, response_content, usage
    )

    point = (
        Point("analytics")
        .tag("model", model)
        .tag("deployment", deployment)
        .tag("project_id", project_id)
        .tag(
            "language",
            "undefined"
            if not chat_id
            else detect_lang(request, response, request_type),
        )
        .tag("upstream", to_string(upstream_url))
        .tag("topic", topic)
        .tag("title", to_string(user_title))
        .tag(
            "response_id",
            response["id"]
            if request_type == RequestType.CHAT_COMPLETION
            else uuid4(),
        )
        .field("user_hash", to_string(user_hash))
        .field("price", price)
        .field(
            "number_request_messages",
            len(request["messages"])
            if request_type == RequestType.CHAT_COMPLETION
            else (1 if request["input"] is str else len(request["input"])),
        )
        .field("chat_id", to_string(chat_id))
        .time(timedelta(milliseconds=timestamp_ms))
    )

    if usage is not None:
        point.field(
            "completion_tokens",
            usage["completion_tokens"] if "completion_tokens" in usage else 0,
        )
        point.field(
            "prompt_tokens",
            usage["prompt_tokens"] if "prompt_tokens" in usage else 0,
        )
    else:
        point.field("completion_tokens", 0)
        point.field("prompt_tokens", 0)

    return point


async def parse_usage_per_model(response: dict):
    statistics = response.get("statistics", None)
    if statistics is None:
        return []

    if statistics is dict or "usage_per_model" not in statistics:
        return []

    usage_per_model = statistics["usage_per_model"]
    if usage_per_model is not list:
        return []

    return usage_per_model


async def on_message(
    logger: Logger,
    influx_write_api: WriteApiAsync,
    deployment: str,
    model: str,
    project_id: str,
    chat_id: str,
    upstream_url: str,
    user_hash: str,
    user_title: str,
    timestamp_ms: int,
    request: dict,
    response: dict,
    type: RequestType,
):
    logger.info(f"Chat completion response length {len(response)}")

    usage_per_model = await parse_usage_per_model(response)

    if len(usage_per_model) == 0:
        point = make_point(
            deployment,
            model,
            project_id,
            chat_id,
            upstream_url,
            user_hash,
            user_title,
            timestamp_ms,
            request,
            response,
            type,
            response.get("usage", None),
        )
        await influx_write_api.write(influx_bucket, record=point)
    else:
        point = make_point(
            deployment,
            model,
            project_id,
            chat_id,
            upstream_url,
            user_hash,
            user_title,
            timestamp_ms,
            request,
            response,
            type,
            None,
        )
        await influx_write_api.write(influx_bucket, record=point)

        for usage in usage_per_model:
            point = make_point(
                deployment,
                usage["model"],
                project_id,
                None,
                None,
                user_hash,
                user_title,
                timestamp_ms,
                request,
                response,
                type,
                usage,
            )
            await influx_write_api.write(influx_bucket, record=point)
