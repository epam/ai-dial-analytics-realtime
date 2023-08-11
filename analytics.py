from influxdb_client import Point, WritePrecision
from datetime import datetime
import os
from logging import Logger
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from topic_model import get_topic

from langid.langid import LanguageIdentifier, model
identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)

def detect_lang(request, response):
    try:
        print(response['choices'][0])
        text = request['messages'][-1]['content'] + '\n\n' + response['choices'][0]['message']['content']

        lang, prob = identifier.classify(text)

        if prob > 0.998:
            return lang

        return 'undefined'
    except:
        return 'undefined'

influx_org = os.environ.get('INFLUX_ORG')
influx_bucket = os.environ.get('INFLUX_BUCKET')


def make_point(deployment: str,
               model: str,
               project_id: str,
               chat_id: str,
               request: any,
               response: any):
    response_content = response['choices'][0]['message']['content']
    topic = get_topic(request['messages'], response_content)

    point = (Point('analytics')
        .tag('model', model)
        .tag('deployment', deployment)
        .tag('model', model)
        .tag('project_id', project_id)
        .tag('language', detect_lang(request, response))
        .tag('upstream', 'undefined')
        .tag('topic', topic)
        .field('user_hash', 'undefined')
        .field('number_request_messages', len(request['messages']))
        .time(datetime.utcnow(), WritePrecision.NS))

    point.field('chat_id', chat_id if len(chat_id) > 0 else 'undefined')

    usage = response['usage']
    if usage != None and 'completion_tokens' in usage and 'prompt_tokens' in usage:
        point.field('completion_tokens', usage['completion_tokens']) \
            .field('prompt_tokens', usage['prompt_tokens'])
    else:
        point.field('completion_tokens', 0) \
            .field('prompt_tokens', 0)

    return point


async def on_message(logger: Logger,
                     influx_write_api: InfluxDBClientAsync,
                     deployment: str,
                     model: str,
                     project_id: str,
                     chat_id: str,
                     request: any,
                     response: any):
    logger.info(f'Chat completion response length {len(response)}')

    point = make_point(deployment, model, project_id, chat_id, request, response)

    await influx_write_api.write(influx_bucket, influx_org, point)
