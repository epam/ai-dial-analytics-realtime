import os

from bertopic import BERTopic

from aidial_analytics_realtime.utils.concurrency import (
    run_in_cpu_tasks_executor,
)
from aidial_analytics_realtime.utils.logging import app_logger as logger
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

    async def get_topic_by_text(self, text: str) -> str | None:
        try:
            return await run_in_cpu_tasks_executor(
                self._get_topic_by_text, text
            )
        except Exception as e:
            logger.error(f"topic: failed to determine topic: {e}")
            return None

    def _get_topic_by_text(self, text: str) -> str | None:
        text = text.strip()
        if not text:
            return None

        with Timer(logger.debug, format="topic {elapsed}"):
            topics, _ = self.model.transform([text])
            topic = self.model.get_topic_info(topics[0])

            if "GeneratedName" in topic:
                # "GeneratedName" is an expected name for the human readable topic representation
                return topic["GeneratedName"][0][0][0]  # type: ignore

            return topic["Name"][0]  # type: ignore
