import json
import logging
import re
from datetime import datetime, timezone

import dateutil.parser as dateutil_parser
import uvicorn
from fastapi import Depends, FastAPI, Request

from aidial_analytics_realtime.analytics import RequestType, on_message
from aidial_analytics_realtime.influx_writer import (
    InfluxWriterAsync,
    create_influx_writer,
)
from aidial_analytics_realtime.rates import RatesCalculator
from aidial_analytics_realtime.topic_model import TopicModel
from aidial_analytics_realtime.universal_api_utils import merge

RATE_PATTERN = r"/v1/rate"
CHAT_COMPLETION_PATTERN = r"/openai/deployments/(.+?)/chat/completions"
EMBEDDING_PATTERN = r"/openai/deployments/(.+?)/embeddings"


app = FastAPI()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@app.on_event("startup")
async def startup_event():
    influx_client, influx_writer = create_influx_writer()
    app.state.influx_client = influx_client
    app.dependency_overrides[InfluxWriterAsync] = lambda: influx_writer

    topic_model = TopicModel()
    app.dependency_overrides[TopicModel] = lambda: topic_model

    rates_calculator = RatesCalculator()
    app.dependency_overrides[RatesCalculator] = lambda: rates_calculator


@app.on_event("shutdown")
async def shutdown_event():
    await app.state.influx_client.close()


async def on_rate_message(request, response):
    logger.info(f"Rate message length {len(request) + len(response)}")


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
):
    if response["status"] != "200":
        return

    request_body = json.loads(request["body"])
    stream = request_body.get("stream", False)
    model = request_body.get("model", deployment)

    response_body = None
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
            response_body["choices"][i]["message"] = response_body["choices"][
                i
            ]["delta"]
            del response_body["choices"][i]["delta"]
    else:
        response_body = json.loads(response["body"])

    await on_message(
        logger,
        influx_writer,
        deployment,
        model,
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
):
    if response["status"] != "200":
        return

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
        json.loads(request["body"]),
        json.loads(response["body"]),
        RequestType.EMBEDDING,
        topic_model,
        rates_calculator,
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

    timestamp = dateutil_parser.isoparse(request["time"])
    if timestamp.tzinfo is None:
        # The logs may come without the timezone information. We want it to be interpreted as UTC, not local time.
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    match = re.search(RATE_PATTERN, uri)
    if match:
        await on_rate_message(request, response)

    match = re.search(CHAT_COMPLETION_PATTERN, uri)
    if match:
        deployment = match.group(1)
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
        )

    match = re.search(EMBEDDING_PATTERN, uri)
    if match:
        deployment = match.group(1)
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
        )


@app.post("/data")
async def on_log_messages(
    request: Request,
    influx_writer: InfluxWriterAsync = Depends(),
    topic_model: TopicModel = Depends(),
    rates_calculator: RatesCalculator = Depends(),
):
    data = await request.json()

    for item in data:
        try:
            await on_log_message(
                json.loads(item["message"]),
                influx_writer,
                topic_model,
                rates_calculator,
            )
        except Exception as e:
            logging.exception(e)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, port=5000)
