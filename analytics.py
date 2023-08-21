import os
import rates

from influxdb_client import Point
from logging import Logger
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from topic_model import get_topic, get_topic_by_text
from enum import Enum
from uuid import uuid4

from langid.langid import LanguageIdentifier, model
identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)

class RequestType(Enum):
    CHAT_COMPLETION = 1
    EMBEDDING = 2

def detect_lang(request, response, request_type):
    if request_type == RequestType.CHAT_COMPLETION:
        text = request['messages'][-1]['content'] + '\n\n' + response['choices'][0]['message']['content']
    else:
        text = request['input'] if type(request['input']) == str else "\n\n".join(request['input'])

    return detect_lang_by_text(text)

def detect_lang_by_text(text):
    try:
        lang, prob = identifier.classify(text)

        if prob > 0.998:
            return lang

        return 'undefined'
    except:
        return 'undefined'

influx_org = os.environ.get('INFLUX_ORG')
influx_bucket = os.environ.get('INFLUX_BUCKET')

def is_empty(obj: str):
    return obj == None or len(obj) == 0

def to_string(obj: str):
    return 'undefined' if is_empty(obj) else str(obj)

def make_point(deployment: str,
               model: str,
               project_id: str,
               chat_id: str,
               upstream_url: str,
               user_hash: str,
               user_title: str,
               timestamp_ms: int,
               request: any,
               response: any,
               request_type: RequestType,
               usage: any):
    topic = None
    response_content = ''
    request_content = ''
    if request_type == RequestType.CHAT_COMPLETION:
        response_content = response['choices'][0]['message']['content']
        request_content = "\n".join([message['content'] for message in request['messages']])
        if not is_empty(chat_id):
            topic = get_topic(request['messages'], response_content)
    else:
        request_content = request['input'] if type(request['input']) == str else "\n".join(request['input'])
        if not is_empty(chat_id):
            topic = get_topic_by_text(request['input'] if type(request['input']) == str else "\n\n".join(request['input']))

    price = rates.calculate_price(model, request_content, response_content, usage)

    point = (Point('analytics')
        .tag('model', model)
        .tag('deployment', deployment)
        .tag('project_id', project_id)
        .tag('language', 'undefined' if is_empty(chat_id) else detect_lang(request, response, request_type))
        .tag('upstream', to_string(upstream_url))
        .tag('topic', topic)
        .tag('title', to_string(user_title))
        .tag('response_id', response['id'] if request_type == RequestType.CHAT_COMPLETION else uuid4())
        .field('user_hash', to_string(user_hash))
        .field('price', price)
        .field('number_request_messages', len(request['messages']) if request_type == RequestType.CHAT_COMPLETION else (1 if type(request['input']) == str else len(request['input'])))
        .field('chat_id', to_string(chat_id))
        .time(timestamp_ms * (10 ** 6)))

    if usage != None:
        point.field('completion_tokens', usage['completion_tokens'] if 'completion_tokens' in usage else 0)
        point.field('prompt_tokens', usage['prompt_tokens'] if 'prompt_tokens' in usage else 0)
    else:
        point.field('completion_tokens', 0)
        point.field('prompt_tokens', 0)

    return point

async def parse_usage_per_model(response: any):
    statistics = response.get('statistics', None)
    if statistics == None:
        return []
    
    if type(statistics) != dict or 'usage_per_model' not in statistics:
        return []
    
    usage_per_model = statistics['usage_per_model']
    if type(usage_per_model) != list:
        return []
    
    return usage_per_model


async def on_message(logger: Logger,
                     influx_write_api: InfluxDBClientAsync,
                     deployment: str,
                     model: str,
                     project_id: str,
                     chat_id: str,
                     upstream_url: str,
                     user_hash: str,
                     user_title: str,
                     timestamp_ms: int,
                     request: any,
                     response: any,
                     type: RequestType):
    logger.info(f'Chat completion response length {len(response)}')

    usage_per_model = await parse_usage_per_model(response)

    if len(usage_per_model) == 0:
        point = make_point(deployment, model, project_id, chat_id, upstream_url, user_hash, user_title, timestamp_ms, request, response, type, response.get('usage', None))
        await influx_write_api.write(influx_bucket, influx_org, point)
    else:
        point = make_point(deployment, model, project_id, chat_id, upstream_url, user_hash, user_title, timestamp_ms, request, response, type, None)
        await influx_write_api.write(influx_bucket, influx_org, point)

        for usage in usage_per_model:
            point = make_point(deployment, usage['model'], project_id, None, None, user_hash, user_title, timestamp_ms, request, response, type, usage)
            await influx_write_api.write(influx_bucket, influx_org, point)
