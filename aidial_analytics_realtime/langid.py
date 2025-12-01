from functools import cache

from langid.langid import LanguageIdentifier, model

from aidial_analytics_realtime.utils.concurrency import (
    run_in_cpu_tasks_executor,
)
from aidial_analytics_realtime.utils.logging import app_logger as logger
from aidial_analytics_realtime.utils.timer import Timer


@cache
def _get_language_identifier() -> LanguageIdentifier:

    return LanguageIdentifier.from_modelstring(model, norm_probs=True)


async def detect_lang_by_text(text: str) -> str | None:
    text = text.strip()

    if not text:
        return None

    try:
        with Timer(logger.debug, format="langid {elapsed}"):
            lang, prob = await run_in_cpu_tasks_executor(
                _get_language_identifier().classify, text
            )

        if prob > 0.998:
            return lang
    except Exception:
        logger.exception("langid: failed to detect language")

    return None
