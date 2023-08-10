from fastapi import FastAPI, Request
import logging
import uvicorn
import os
import json
import re
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client.client.write_api import ASYNCHRONOUS

RATE_PATTERN = r"/v1/rate"
CHAT_COMPLETION_PATTERN = r"/openai/deployments/(.+?)/chat/completions"

influx_url = os.environ.get('INFLUX_URL')
influx_api_token = os.environ.get('INFLUX_API_TOKEN')
influx_org = os.environ.get('INFLUX_ORG')
influx_bucket = os.environ.get('INFLUX_BUCKET')

app = FastAPI()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@app.on_event("startup")
async def startup_event():
    global client, write_api
    
    client = InfluxDBClientAsync(url=influx_url, token=influx_api_token, org=influx_org)
    write_api = client.write_api()

@app.on_event("shutdown")
async def shutdown_event():
    await client.close()

async def on_rate_message(request, response):
    logger.info(f'Rate message length {len(request) + len(response)}')

async def publish_usage(deployment, model, project_id, chat_id, usage):
    logger.info(f'Chat completion message length {usage["total_tokens"]}')

    data = [
        f"tokens,deployment={deployment},model={model},project_id={project_id} completion_tokens={usage['completion_tokens']}",
        f"tokens,deployment={deployment},model={model},project_id={project_id} prompt_tokens={usage['prompt_tokens']}",
    ]
    await write_api.write(influx_bucket, influx_org, data)


async def on_chat_completion_message(deployment, project_id, chat_id, request, response):
    if response['status'] != '200':
        return

    request_body = json.loads(request['body'])
    stream = request_body.get('stream', False)
    model = request_body.get('model', deployment)

    if stream:
        body = response['body']
        chunks = body.split('\n\ndata: ')

        chunks[0] = chunks[0].removeprefix('data: ')
        chunks = chunks[0:len(chunks)-1] # remove [DONE] chunk

        for chunk in chunks:
            chunk = json.loads(chunk)

            if 'usage' in chunk and chunk['usage'] != None:
                await publish_usage(deployment, model, project_id, chat_id, chunk['usage'])
    else:
        body_json = json.loads(response['body'])

        if 'usage' in body_json and body_json['usage'] != None:
            await publish_usage(deployment, model, project_id, chat_id, body_json['usage'])


async def on_new_message(message):
    request = message['request']
    uri = message['request']['uri']
    response = message['response']
    project_id = message['project']['id']
    chat_id = message['chat']['id']

    match = re.search(RATE_PATTERN, uri)
    if match:
        await on_rate_message(request, response)

    match = re.search(CHAT_COMPLETION_PATTERN, uri)
    if match:
        deployment = match.group(1)
        await on_chat_completion_message(deployment, project_id, chat_id, request, response)

@app.post('/data')
async def chat(request: Request):
    data = await request.json()

    for item in data:
        await on_new_message(json.loads(item['message']))

@app.get('/health')
def health():
    return {
        'status': 'ok'
    }

if __name__ == '__main__':
    uvicorn.run(app, port=5000)
