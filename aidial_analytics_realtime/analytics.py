from datetime import datetime
from decimal import Decimal
from enum import Enum
from logging import Logger
from typing import Awaitable, Callable
from uuid import uuid4

from influxdb_client import Point
from langid.langid import LanguageIdentifier, model
from typing_extensions import assert_never

from aidial_analytics_realtime.dial import (
    get_chat_completion_request_contents,
    get_chat_completion_response_contents,
    get_embeddings_request_contents,
)
from aidial_analytics_realtime.rates import RatesCalculator
from aidial_analytics_realtime.topic_model import TopicModel
from aidial_analytics_realtime.utils.concurrency import (
    run_in_cpu_tasks_executor,
)

identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)


class RequestType(Enum):
    CHAT_COMPLETION = 1
    EMBEDDING = 2


async def detect_lang(
    logger: Logger, request: dict, response: dict, request_type: RequestType
) -> str:
    match request_type:
        case RequestType.CHAT_COMPLETION:
            request_contents = get_chat_completion_request_contents(
                logger, request
            )
            response_content = get_chat_completion_response_contents(
                logger, response
            )
            text = "\n\n".join(request_contents[-1:] + response_content)
        case RequestType.EMBEDDING:
            text = "\n\n".join(get_embeddings_request_contents(logger, request))
        case _:
            assert_never(request_type)

    return to_string(await detect_lang_by_text(text))


async def detect_lang_by_text(text: str) -> str | None:
    text = text.strip()

    if not text:
        return None

    try:
        lang, prob = await run_in_cpu_tasks_executor(identifier.classify, text)
        if prob > 0.998:
            return lang
    except Exception:
        pass

    return None


def to_string(obj: str | None) -> str:
    return obj or "undefined"


def build_execution_path(path: list | None):
    return "undefined" if not path else "/".join(map(to_string, path))


async def make_point(
    logger: Logger,
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
    rates_calculator: RatesCalculator,
    parent_deployment: str | None,
    trace: dict | None,
    execution_path: list | None,
):
    topic = None
    response_content = ""
    request_content = ""

    if response is not None and request is not None:
        match request_type:
            case RequestType.CHAT_COMPLETION:
                response_contents = get_chat_completion_response_contents(
                    logger, response
                )
                request_contents = get_chat_completion_request_contents(
                    logger, request
                )

                request_content = "\n".join(request_contents)
                response_content = "\n".join(response_contents)

                if chat_id:
                    topic = to_string(
                        await topic_model.get_topic_by_text(
                            "\n\n".join(request_contents + response_contents)
                        )
                    )
            case RequestType.EMBEDDING:
                request_contents = get_embeddings_request_contents(
                    logger, request
                )

                request_content = "\n".join(request_contents)
                if chat_id:
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
    else:
        price = rates_calculator.calculate_price(
            deployment, model, request_content, response_content, usage
        )

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
                else await detect_lang(logger, request, response, request_type)
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
                else uuid4()
            ),
        )
        .field("user_hash", to_string(user_hash))
        .field("price", price)
        .field("deployment_price", deployment_price)
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


async def parse_usage_per_model(response: dict | None):
    if response is None:
        return []

    statistics = response.get("statistics")
    if statistics is None:
        return []

    if not isinstance(statistics, dict) or "usage_per_model" not in statistics:
        return []

    usage_per_model = statistics["usage_per_model"]
    if not isinstance(usage_per_model, list):
        return []

    return usage_per_model


async def on_message(
    logger: Logger,
    influx_writer: Callable[[Point], Awaitable[None]],
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
    rates_calculator: RatesCalculator,
    token_usage: dict | None,
    parent_deployment: str | None,
    trace: dict | None,
    execution_path: list | None,
):
    logger.info(f"Chat completion response length {len(response or [])}")

    usage_per_model = await parse_usage_per_model(response)
    response_usage = None if response is None else response.get("usage")

    if token_usage is not None:
        point = await make_point(
            logger,
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
            token_usage,
            topic_model,
            rates_calculator,
            parent_deployment,
            trace,
            execution_path,
        )
        await influx_writer(point)
    elif len(usage_per_model) == 0:
        point = await make_point(
            logger,
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
            response_usage,
            topic_model,
            rates_calculator,
            parent_deployment,
            trace,
            execution_path,
        )
        await influx_writer(point)
    else:
        point = await make_point(
            logger,
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
            None,
            topic_model,
            rates_calculator,
            parent_deployment,
            trace,
            execution_path,
        )
        await influx_writer(point)

        for usage in usage_per_model:
            point = await make_point(
                logger,
                deployment,
                usage["model"],
                project_id,
                None,
                None,
                user_hash,
                user_title,
                timestamp,
                request,
                response,
                type,
                usage,
                topic_model,
                rates_calculator,
                parent_deployment,
                trace,
                execution_path,
            )
            await influx_writer(point)
