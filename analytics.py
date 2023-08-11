from influxdb_client import Point, WritePrecision
from datetime import datetime
import os
from logging import Logger
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

influx_org = os.environ.get('INFLUX_ORG')
influx_bucket = os.environ.get('INFLUX_BUCKET')

async def on_message(logger: Logger,
                     influx_write_api: InfluxDBClientAsync,
                     deployment: str,
                     model: str,
                     project_id: str,
                     chat_id: str,
                     request: any,
                     response: any):
    usage = response['usage']

    logger.info(f'Chat completion response length {len(response)}')

    point = Point('analytics') \
        .tag('model', model) \
        .tag('deployment', deployment) \
        .tag('model', model) \
        .tag('project_id', project_id) \
        .tag('language', 'English') \
        .tag('upstream', 'undefined') \
        .tag('topic', 'general') \
        .field('user_hash', 'undefined') \
        .field('number_request_messages', len(request['messages'])) \
        .time(datetime.utcnow(), WritePrecision.NS)

    if len(chat_id) > 0:
        point.field('chat_id', chat_id)
    else:
        point.field('chat_id', 'undefined')

    if usage != None:
        point.field('completion_tokens', usage['completion_tokens']) \
            .field('prompt_tokens', usage['prompt_tokens'])
    else:
        point.field('completion_tokens', 0) \
            .field('prompt_tokens', 0)

    await influx_write_api.write(influx_bucket, influx_org, point)