import os
from typing import Protocol

from bertopic import BERTopic

from aidial_analytics_realtime.utils.concurrency import (
    run_in_cpu_tasks_executor,
)
from aidial_analytics_realtime.utils.logging import app_logger as logger
from aidial_analytics_realtime.utils.timer import Timer


class TopicModel(Protocol):
    async def get_topic_by_text(self, text: str) -> str | None: ...


class TopicModelNoOp:
    async def get_topic_by_text(self, text: str) -> str | None:
        return None


class TopicModelBERT:
    model: BERTopic

    def __init__(self, model: BERTopic):
        self.model = model

    @classmethod
    def create(
        cls, *, topic_model: str, topic_embeddings_model: str | None
    ) -> "TopicModelBERT":

        model = BERTopic.load(topic_model, topic_embeddings_model)

        # Disable tqdm progress bars on batch encoding
        model.verbose = False

        # Make sure the model is loaded
        model.transform(["test"])

        return cls(model=model)

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


def create_topic_model(
    *,
    topic_model: str | None = None,
    topic_embeddings_model: str | None = None,
) -> TopicModel:
    topic_model = topic_model or os.getenv("TOPIC_MODEL") or None

    if topic_model is None:
        return TopicModelNoOp()

    topic_embeddings_model = topic_embeddings_model or os.getenv(
        "TOPIC_EMBEDDINGS_MODEL"
    ) or None

    return TopicModelBERT.create(
        topic_model=topic_model,
        topic_embeddings_model=topic_embeddings_model,
    )
