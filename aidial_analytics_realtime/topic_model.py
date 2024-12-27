import logging
import os

from bertopic import BERTopic

from aidial_analytics_realtime.utils.log_config import with_prefix
from aidial_analytics_realtime.utils.timer import Timer


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

        # Disable tqdm progress bars on batch encoding
        self.model.verbose = False

        # Make sure the model is loaded
        self.model.transform(["test"])

    def get_topic_by_text(self, logger: logging.Logger, text):
        with Timer(with_prefix(logger, "[topic]").info):
            topics, _ = self.model.transform([text])
            topic = self.model.get_topic_info(topics[0])

            if "GeneratedName" in topic:
                # "GeneratedName" is an expected name for the human readable topic representation
                return topic["GeneratedName"][0][0][0]

            return topic["Name"][0]
