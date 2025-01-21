import logging

from langid.langid import LanguageIdentifier, model

from aidial_analytics_realtime.utils.concurrency import (
    run_in_cpu_tasks_executor,
)
from aidial_analytics_realtime.utils.timer import Timer

_logger = logging.getLogger("app.langid")
_identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)


async def detect_lang_by_text(text: str) -> str | None:
    text = text.strip()

    if not text:
        return None

    try:
        with Timer(_logger.debug):
            lang, prob = await run_in_cpu_tasks_executor(
                _identifier.classify, text
            )

        if prob > 0.998:
            return lang
    except Exception:
        _logger.exception("failed to detect language")

    return None
