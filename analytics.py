from influxdb_client import Point, WritePrecision
from datetime import datetime
import os
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

def to_string(obj: str):
    return 'undefined' if obj == None or len(obj) == 0 else str(obj)

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
               request_type: RequestType):
    topic = None
    if request_type == RequestType.CHAT_COMPLETION:
        response_content = response['choices'][0]['message']['content']
        topic = get_topic(request['messages'], response_content)
    else:
        topic = get_topic_by_text(request['input'] if type(request['input']) == str else "\n\n".join(request['input']))

    point = (Point('analytics')
        .tag('model', model)
        .tag('deployment', deployment)
        .tag('project_id', project_id)
        .tag('language', detect_lang(request, response, request_type))
        .tag('upstream', to_string(upstream_url))
        .tag('topic', topic)
        .tag('title', to_string(user_title))
        .tag('response_id', response['id'] if request_type == RequestType.CHAT_COMPLETION else uuid4())
        .field('user_hash', to_string(user_hash))
        .field('number_request_messages', len(request['messages']) if request_type == RequestType.CHAT_COMPLETION else (1 if type(request['input']) == str else len(request['input'])))
        .field('chat_id', to_string(chat_id))
        .time(timestamp_ms * (10 ** 6)))

    usage = response.get('usage', None)
    if usage != None:
        point.field('completion_tokens', usage['completion_tokens'] if 'completion_tokens' in usage else 0)
        point.field('prompt_tokens', usage['prompt_tokens'] if 'prompt_tokens' in usage else 0)

    return point


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

    point = make_point(deployment, model, project_id, chat_id, upstream_url, user_hash, user_title, timestamp_ms, request, response, type)

    # await influx_write_api.write(influx_bucket, influx_org, point)
