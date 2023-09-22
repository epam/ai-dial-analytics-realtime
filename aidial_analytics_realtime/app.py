import json
import logging
import os
import re

import uvicorn
from dateutil import parser
from fastapi import FastAPI, Request
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from aidial_analytics_realtime.analytics import RequestType, on_message
from aidial_analytics_realtime.universal_api_utils import merge

RATE_PATTERN = r"/v1/rate"
CHAT_COMPLETION_PATTERN = r"/openai/deployments/(.+?)/chat/completions"
EMBEDDING_PATTERN = r"/openai/deployments/(.+?)/embeddings"

influx_url = os.environ["INFLUX_URL"]
influx_api_token = os.environ.get("INFLUX_API_TOKEN")
influx_org = os.environ["INFLUX_ORG"]

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
    global client, influx_write_api

    client = InfluxDBClientAsync(
        url=influx_url, token=influx_api_token, org=influx_org
    )
    influx_write_api = client.write_api()


@app.on_event("shutdown")
async def shutdown_event():
    await client.close()


async def on_rate_message(request, response):
    logger.info(f"Rate message length {len(request) + len(response)}")


async def on_chat_completion_message(
    deployment: str,
    project_id: str,
    chat_id: str,
    upstream_url: str,
    user_hash: str,
    user_title: str,
    timestamp_ms: int,
    request: dict,
    response: dict,
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
        influx_write_api,
        deployment,
        model,
        project_id,
        chat_id,
        upstream_url,
        user_hash,
        user_title,
        timestamp_ms,
        request_body,
        response_body,
        RequestType.CHAT_COMPLETION,
    )


async def on_embedding_message(
    deployment: str,
    project_id: str,
    chat_id: str,
    upstream_url: str,
    user_hash: str,
    user_title: str,
    timestamp_ms: int,
    request: dict,
    response: dict,
):
    if response["status"] != "200":
        return

    await on_message(
        logger,
        influx_write_api,
        deployment,
        deployment,
        project_id,
        chat_id,
        upstream_url,
        user_hash,
        user_title,
        timestamp_ms,
        json.loads(request["body"]),
        json.loads(response["body"]),
        RequestType.EMBEDDING,
    )


async def on_log_message(message):
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
    timestamp_ms = int(parser.parse(request["time"]).timestamp() * (10**3))

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
            timestamp_ms,
            request,
            response,
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
            timestamp_ms,
            request,
            response,
        )


@app.post("/data")
async def on_log_messages(request: Request):
    data = await request.json()

    for item in data:
        try:
            await on_log_message(json.loads(item["message"]))
        except Exception as e:
            logging.exception(e)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, port=5000)
