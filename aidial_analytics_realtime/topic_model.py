import os

from bertopic import BERTopic

from aidial_analytics_realtime.utils.concurrency import (
    run_in_cpu_tasks_executor,
)


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

        # Make sure the model is loaded
        self._get_topic_by_text("test")

    async def get_topic_by_text(self, text: str) -> str:
        return await run_in_cpu_tasks_executor(self._get_topic_by_text, text)

    def _get_topic_by_text(self, text: str) -> str:
        topics, _ = self.model.transform([text])
        topic = self.model.get_topic_info(topics[0])

        if "GeneratedName" in topic:
            # "GeneratedName" is an expected name for the human readable topic representation
            return topic["GeneratedName"][0][0][0]  # type: ignore

        return topic["Name"][0]  # type: ignore
