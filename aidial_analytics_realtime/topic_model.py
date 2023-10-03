import os

from bertopic import BERTopic


class TopicModel:
    def __init__(
        self,
        topic_model_name: str | None = None,
        topic_embeddings_model_name: str | None = None,
    ):
        if not topic_model_name:
            topic_model_name = os.environ.get("TOPIC_MODEL", "./topic_model")
            topic_embeddings_model_name = os.environ.get(
                "TOPIC_EMBEDDINGS_MODEL", None
            )
        assert topic_model_name is not None
        self.model = BERTopic.load(
            topic_model_name, topic_embeddings_model_name
        )
        self.model.transform(["test"])  # Make sure the model is loaded

    def get_topic(self, request_messages, response_content):
        text = "\n\n".join(
            [message["content"] for message in request_messages]
            + [response_content]
        )

        return self.get_topic_by_text(text)

    def get_topic_by_text(self, text):
        topics, _ = self.model.transform([text])
        topic = self.model.get_topic_info(topics[0])

        if "GeneratedName" in topic:
            # "GeneratedName" is an expected name for the human readable topic representation
            return topic["GeneratedName"][0][0][0]

        return topic["Name"][0]
