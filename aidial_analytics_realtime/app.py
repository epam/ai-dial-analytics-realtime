import asyncio
import contextlib
import json
import logging
import re
import sys
from datetime import datetime
from typing import Any

import aiohttp
import starlette.requests
import uvicorn
from aidial_sdk.telemetry.init import init_telemetry
from aidial_sdk.telemetry.types import TelemetryConfig
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from aidial_analytics_realtime.analytics import (
    RequestType,
    make_mcp_point,
    make_rate_point,
    make_route_point,
    on_message,
)
from aidial_analytics_realtime.influx_writer import (
    InfluxWriterAsync,
    create_influx_writer,
)
from aidial_analytics_realtime.langid import LangID
from aidial_analytics_realtime.log_request.message import get_assembled_response
from aidial_analytics_realtime.time import parse_time
from aidial_analytics_realtime.topic_model import TopicModel, create_topic_model
from aidial_analytics_realtime.utils.concurrency import cpu_task_executor
from aidial_analytics_realtime.utils.deprecations import check_deprecations
from aidial_analytics_realtime.utils.logging import (
    add_logger_prefix,
    configure_loggers,
)
from aidial_analytics_realtime.utils.logging import app_logger as logger
from aidial_analytics_realtime.utils.request import (
    DataRequest,
    Message,
    get_tracing_ids,
)
from aidial_analytics_realtime.utils.timer import Timer

RATE_PATTERN = r"/v1/(.+?)/rate"
CHAT_COMPLETION_PATTERN = r"/openai/deployments/(.+?)/chat/completions"
EMBEDDING_PATTERN = r"/openai/deployments/(.+?)/embeddings"
MCP_PATTERN = r"/v1/(toolset|deployments)/(.+?)/mcp"
ROUTES_PATTERN = r"^/v1/deployments/(.+?)/route/(.+?)$"


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    influx_client, influx_writer = create_influx_writer()
    with cpu_task_executor:
        async with influx_client:
            app.dependency_overrides[InfluxWriterAsync] = lambda: influx_writer

            topic_model = create_topic_model()
            app.dependency_overrides[TopicModel] = lambda: topic_model

            lang_id = LangID.create()
            app.dependency_overrides[LangID] = lambda: lang_id

            yield


app = FastAPI(lifespan=lifespan)

init_telemetry(app, TelemetryConfig())

configure_loggers()

check_deprecations()


async def on_rate_message(
    deployment: str,
    project_id: str,
    chat_id: str,
    user_hash: str,
    user_title: str,
    timestamp: datetime,
    request: dict,
    response: dict,
    influx_writer: InfluxWriterAsync,
):
    request_body = json.loads(request["body"])
    point = make_rate_point(
        deployment,
        project_id,
        chat_id,
        user_hash,
        user_title,
        timestamp,
        request_body,
    )
    await influx_writer(point)


async def on_chat_completion_message(
    deployment: str,
    project_id: str,
    chat_id: str,
    upstream_url: str,
    user_hash: str,
    user_title: str,
    timestamp: datetime,
    request: dict,
    response: dict,
    response_body: dict | None,
    influx_writer: InfluxWriterAsync,
    topic_model: TopicModel,
    lang_id: LangID,
    token_usage: dict | None,
    parent_deployment: str | None,
    trace: dict | None,
    execution_path: list | None,
):
    if response["status"] != "200":
        return

    request_body = None
    model: str | None = None

    if (request_body_str := request.get("body")) is not None:
        request_body = json.loads(request_body_str)
        model = request_body.get("model") or deployment

    await on_message(
        influx_writer,
        deployment,
        model or deployment,
        project_id,
        chat_id,
        upstream_url,
        user_hash,
        user_title,
        timestamp,
        request_body,
        response_body,
        RequestType.CHAT_COMPLETION,
        topic_model,
        lang_id,
        token_usage,
        parent_deployment,
        trace,
        execution_path,
    )


async def on_embedding_message(
    deployment: str,
    project_id: str,
    chat_id: str,
    upstream_url: str,
    user_hash: str,
    user_title: str,
    timestamp: datetime,
    request: dict,
    response: dict,
    influx_writer: InfluxWriterAsync,
    topic_model: TopicModel,
    lang_id: LangID,
    token_usage: dict | None,
    parent_deployment: str | None,
    trace: dict | None,
    execution_path: list | None,
):
    if response["status"] != "200":
        return

    request_body_str = request.get("body")
    response_body_str = response.get("body")

    request_body = (
        None if request_body_str is None else json.loads(request_body_str)
    )
    response_body = (
        None if response_body_str is None else json.loads(response_body_str)
    )

    await on_message(
        influx_writer,
        deployment,
        deployment,
        project_id,
        chat_id,
        upstream_url,
        user_hash,
        user_title,
        timestamp,
        request_body,
        response_body,
        RequestType.EMBEDDING,
        topic_model,
        lang_id,
        token_usage,
        parent_deployment,
        trace,
        execution_path,
    )


async def on_mcp_message(
    *,
    deployment: str,
    project_id: str,
    chat_id: str,
    upstream_url: str,
    user_hash: str,
    user_title: str,
    timestamp: datetime,
    request: dict,
    response: dict,
    influx_writer: InfluxWriterAsync,
    parent_deployment: str | None,
    trace: dict | None,
    execution_path: list | None,
):
    if response["status"] != "200":
        return

    request_body_str = request.get("body")
    request_body = (
        None if request_body_str is None else json.loads(request_body_str)
    )

    point = make_mcp_point(
        deployment=deployment,
        project_id=project_id,
        chat_id=chat_id,
        upstream_url=upstream_url,
        user_hash=user_hash,
        user_title=user_title,
        timestamp=timestamp,
        request=request_body,
        parent_deployment=parent_deployment,
        trace=trace,
        execution_path=execution_path,
    )
    await influx_writer(point)


async def on_routes_message(
    *,
    deployment: str,
    route_path: str,
    project_id: str,
    chat_id: str,
    upstream_url: str,
    user_hash: str,
    user_title: str,
    timestamp: datetime,
    request: dict,
    response: dict,
    influx_writer: InfluxWriterAsync,
    parent_deployment: str | None,
    trace: dict | None,
    execution_path: list | None,
):
    if response["status"] != "200":
        return

    http_method = request["method"]

    point = make_route_point(
        deployment=deployment,
        route_path=route_path,
        http_method=http_method,
        project_id=project_id,
        chat_id=chat_id,
        upstream_url=upstream_url,
        user_hash=user_hash,
        user_title=user_title,
        timestamp=timestamp,
        parent_deployment=parent_deployment,
        trace=trace,
        execution_path=execution_path,
    )
    await influx_writer(point)


async def on_log_message(
    message: dict,
    influx_writer: InfluxWriterAsync,
    topic_model: TopicModel,
    lang_id: LangID,
):
    request = message["request"]
    uri = message["request"]["uri"]
    response = message["response"]
    project_id = message["project"]["id"]
    chat_id = message["chat"]["id"]
    user_hash = message["user"]["id"]
    user_title = message["user"]["title"]
    timestamp = parse_time(request["time"])

    upstream_url = response.get("upstream_uri") or ""
    token_usage = message.get("token_usage")
    trace = message.get("trace")
    parent_deployment = message.get("parent_deployment")
    execution_path = message.get("execution_path")
    deployment = message.get("deployment") or ""

    if re.search(RATE_PATTERN, uri):
        await on_rate_message(
            deployment,
            project_id,
            chat_id,
            user_hash,
            user_title,
            timestamp,
            request,
            response,
            influx_writer,
        )

    elif re.search(CHAT_COMPLETION_PATTERN, uri):
        response_body = get_assembled_response(message)
        await on_chat_completion_message(
            deployment,
            project_id,
            chat_id,
            upstream_url,
            user_hash,
            user_title,
            timestamp,
            request,
            response,
            response_body,
            influx_writer,
            topic_model,
            lang_id,
            token_usage,
            parent_deployment,
            trace,
            execution_path,
        )

    elif re.search(EMBEDDING_PATTERN, uri):
        await on_embedding_message(
            deployment,
            project_id,
            chat_id,
            upstream_url,
            user_hash,
            user_title,
            timestamp,
            request,
            response,
            influx_writer,
            topic_model,
            lang_id,
            token_usage,
            parent_deployment,
            trace,
            execution_path,
        )

    elif re.search(MCP_PATTERN, uri):
        await on_mcp_message(
            deployment=deployment,
            project_id=project_id,
            chat_id=chat_id,
            upstream_url=upstream_url,
            user_hash=user_hash,
            user_title=user_title,
            timestamp=timestamp,
            request=request,
            response=response,
            influx_writer=influx_writer,
            parent_deployment=parent_deployment,
            trace=trace,
            execution_path=execution_path,
        )

    elif m := re.search(ROUTES_PATTERN, uri):
        route_path = f"/{m.group(2)}"
        await on_routes_message(
            deployment=deployment,
            route_path=route_path,
            project_id=project_id,
            chat_id=chat_id,
            upstream_url=upstream_url,
            user_hash=user_hash,
            user_title=user_title,
            timestamp=timestamp,
            request=request,
            response=response,
            influx_writer=influx_writer,
            parent_deployment=parent_deployment,
            trace=trace,
            execution_path=execution_path,
        )

    else:
        logger.warning(f"Unsupported message type: {uri!r}")


@app.post("/data")
async def on_log_messages(
    data: DataRequest,
    influx_writer: InfluxWriterAsync = Depends(),  # noqa: B008
    topic_model: TopicModel = Depends(),  # noqa: B008
    lang_id: LangID = Depends(),  # noqa: B008
):
    messages = data.root
    n = len(messages)
    logger.info(f"number of messages: {n}")

    async with Timer(logger.debug, format="request {elapsed}"):

        async def _task(i: int, message: Any) -> dict:
            trace_id, span_id = get_tracing_ids(message)

            add_logger_prefix(
                f"[{i}/{n}] [trace_id={trace_id or 'na'} span_id={span_id or 'na'}]"  # noqa: E501
            )

            async with Timer(logger.debug, format="message {elapsed}"):
                return await process_message(
                    message,
                    influx_writer,
                    topic_model,
                    lang_id,
                )

        statuses: list[dict] = await asyncio.gather(
            *[_task(i, message) for i, message in enumerate(messages, start=1)]
        )

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"response: {json.dumps(statuses)}")

    # Returning 200 code even if processing of some messages has failed,
    # since the log broker that sends the messages may decide
    # to retry the failed requests.
    return JSONResponse(content=statuses, status_code=200)


async def process_message(
    request_message: Any,
    influx_writer: InfluxWriterAsync,
    topic_model: TopicModel,
    lang_id: LangID,
) -> dict:
    def _error(reason: str | None = None) -> dict:
        error = str(sys.exc_info()[1])
        ret = {"status": "error"}
        if error:
            ret["error"] = error
        if reason:
            ret["reason"] = reason
            logger.error(reason)
        else:
            logger.exception("caught exception")
        return ret

    try:
        message_str = Message.model_validate(request_message).message
    except Exception:
        return _error("invalid request message")

    try:
        message_dict = json.JSONDecoder(strict=False).decode(message_str)
    except Exception:
        return _error("invalid JSON in request message")

    try:
        await on_log_message(message_dict, influx_writer, topic_model, lang_id)
        logger.debug("success")
        return {"status": "success"}
    except starlette.requests.ClientDisconnect:
        return _error("client disconnect")
    except aiohttp.ClientConnectionError:
        return _error("connection error")
    except TimeoutError:
        return _error("timeout")
    except Exception:
        return _error()


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, port=5000)
