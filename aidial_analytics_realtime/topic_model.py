import os
from typing import Any

from bertopic import BERTopic

topic_model_name = os.environ.get("TOPIC_MODEL", "./topic_model")
topic_embeddings_model_name = os.environ.get("TOPIC_EMBEDDINGS_MODEL", None)


topic_model = BERTopic.load(topic_model_name, topic_embeddings_model_name)
topic_model.transform(["test"])  # Make sure the model is loaded


def get_topic(request_messages, response_content):
    text = "\n\n".join(
        [message["content"] for message in request_messages]
        + [response_content]
    )

    return get_topic_by_text(text)


def get_topic_by_text(text):
    topics, _ = topic_model.transform([text])
    topic: Any = topic_model.get_topic_info(topics[0])

    if "GeneratedName" in topic:
        # "GeneratedName" is an expected name for the human readable topic representation
        return topic["GeneratedName"][0][0][0]

    return topic["Name"][0]
