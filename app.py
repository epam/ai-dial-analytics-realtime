from fastapi import FastAPI, Request
import logging
import uvicorn
import os
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client.client.write_api import ASYNCHRONOUS


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
    
    client = InfluxDBClientAsync(url="https://influxdb.staging.deltixhub.io", token=influx_api_token, org=influx_org)
    write_api = client.write_api()

async def on_new_message(message):
    logger.info(f'New message length {len(message)}')

    data = f"tokens,host=dial completion_tokens={len(message)}"
    await write_api.write(influx_bucket, influx_org, data)

@app.post('/data')
async def chat(request: Request):
    data = await request.json()

    for item in data:
        await on_new_message(item['message'])

@app.get('/health')
def health():
    return {
        'status': 'ok'
    }

if __name__ == '__main__':
    uvicorn.run(app, port=5000)
    client.close()