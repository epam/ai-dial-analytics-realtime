import contextlib
import json
import logging
import re
from datetime import datetime

import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from aidial_analytics_realtime.analytics import (
    RequestType,
    make_rate_point,
    on_message,
)
from aidial_analytics_realtime.influx_writer import (
    InfluxWriterAsync,
    create_influx_writer,
)
from aidial_analytics_realtime.rates import RatesCalculator
from aidial_analytics_realtime.time import parse_time
from aidial_analytics_realtime.topic_model import TopicModel
from aidial_analytics_realtime.universal_api_utils import merge
from aidial_analytics_realtime.utils.concurrency import cpu_task_executor
from aidial_analytics_realtime.utils.log_config import configure_loggers, logger

RATE_PATTERN = r"/v1/(.+?)/rate"
CHAT_COMPLETION_PATTERN = r"/openai/deployments/(.+?)/chat/completions"
EMBEDDING_PATTERN = r"/openai/deployments/(.+?)/embeddings"


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    influx_client, influx_writer = create_influx_writer()
    with cpu_task_executor:
        async with influx_client:
            app.dependency_overrides[InfluxWriterAsync] = lambda: influx_writer

            topic_model = TopicModel()
            app.dependency_overrides[TopicModel] = lambda: topic_model

            rates_calculator = RatesCalculator()
            app.dependency_overrides[RatesCalculator] = lambda: rates_calculator

            yield


app = FastAPI(lifespan=lifespan)

configure_loggers()


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
    logger.info(f"Rate message length {len(request) + len(response)}")
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
    influx_writer: InfluxWriterAsync,
    topic_model: TopicModel,
    rates_calculator: RatesCalculator,
    token_usage: dict | None,
    parent_deployment: str | None,
    trace: dict | None,
    execution_path: list | None,
):
    if response["status"] != "200":
        return

    response_body = None
    request_body = None
    model: str | None = None

    if (request_body_str := request.get("body")) is not None:

        request_body = json.loads(request_body_str)
        stream = request_body.get("stream", False)
        model = request_body.get("model", deployment)

        if stream:
            body = response["body"]
            chunks = body.split("\n\ndata: ")

            chunks = [chunk.strip() for chunk in chunks]

            chunks[0] = chunks[0][chunks[0].find("data: ") + 6 :]
            if chunks[-1] == "[DONE]":
                chunks.pop(len(chunks) - 1)

            response_body = json.loads(chunks[-1])
            for chunk in chunks[0 : len(chunks) - 1]:
                chunk = json.loads(chunk)

                response_body["choices"] = merge(
                    response_body["choices"], chunk["choices"]
                )

            for i in range(len(response_body["choices"])):
                response_body["choices"][i]["message"] = response_body[
                    "choices"
                ][i]["delta"]
                del response_body["choices"][i]["delta"]
        else:
            response_body = json.loads(response["body"])

    await on_message(
        logger,
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
        rates_calculator,
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
    rates_calculator: RatesCalculator,
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
        logger,
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
        rates_calculator,
        token_usage,
        parent_deployment,
        trace,
        execution_path,
    )


async def on_log_message(
    message: dict,
    influx_writer: InfluxWriterAsync,
    topic_model: TopicModel,
    rates_calculator: RatesCalculator,
):
    request = message["request"]
    uri = message["request"]["uri"]
    response = message["response"]
    project_id = message["project"]["id"]
    chat_id = message["chat"]["id"]
    user_hash = message["user"]["id"]
    user_title = message["user"]["title"]
    upstream_url = (
        response["upstream_uri"] if "upstream_uri" in response else ""
    )

    timestamp = parse_time(request["time"])

    token_usage = message.get("token_usage", None)
    trace = message.get("trace", None)
    parent_deployment = message.get("parent_deployment", None)
    execution_path = message.get("execution_path", None)
    deployment = message.get("deployment", "")

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
            influx_writer,
            topic_model,
            rates_calculator,
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
            rates_calculator,
            token_usage,
            parent_deployment,
            trace,
            execution_path,
        )

    else:
        logger.warning(f"Unsupported message type: {uri!r}")


@app.post("/data")
async def on_log_messages(
    request: Request,
    influx_writer: InfluxWriterAsync = Depends(),
    topic_model: TopicModel = Depends(),
    rates_calculator: RatesCalculator = Depends(),
):
    data = await request.json()

    statuses = []
    for idx, item in enumerate(data):
        try:
            await on_log_message(
                json.loads(item["message"]),
                influx_writer,
                topic_model,
                rates_calculator,
            )
        except Exception as e:
            logging.exception(f"Error processing message #{idx}")
            statuses.append({"status": "error", "error": str(e)})
        else:
            statuses.append({"status": "success"})

    # Returning 200 code even if processing of some messages has failed,
    # since the log broker that sends the messages may decide to retry the failed requests.
    return JSONResponse(content=statuses, status_code=200)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, port=5000)
