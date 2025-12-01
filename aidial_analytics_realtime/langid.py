from typing import Callable, Self, Tuple

from aidial_analytics_realtime.utils.concurrency import (
    run_in_cpu_tasks_executor,
)
from aidial_analytics_realtime.utils.logging import app_logger as logger
from aidial_analytics_realtime.utils.timer import Timer

_Classifier = Callable[[str], Tuple[str, float]]


class LangID:
    classify: _Classifier

    def __init__(self, classify: _Classifier) -> None:
        self.classify = classify

    @classmethod
    def create(cls) -> Self:
        from langid import langid

        identifier = langid.LanguageIdentifier.from_modelstring(
            langid.model, norm_probs=True
        )
        return cls(classify=identifier.classify)

    async def detect_language(self, text: str) -> str | None:
        text = text.strip()

        if not text:
            return None

        try:
            with Timer(logger.debug, format="langid {elapsed}"):
                lang, prob = await run_in_cpu_tasks_executor(
                    self.classify, text
                )

            if prob > 0.998:
                return lang
        except Exception:
            logger.exception("langid: failed to detect language")

        return None
