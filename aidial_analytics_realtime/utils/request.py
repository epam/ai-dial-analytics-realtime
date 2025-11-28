import re
from typing import Any, List, Tuple

from pydantic import BaseModel


class DataRequest(BaseModel):
    __root__: List[Any]


class Message(BaseModel):
    message: str


def get_tracing_ids(request_message: Any) -> Tuple[str | None, str | None]:
    try:
        message = request_message["message"]
        if not isinstance(message, str):
            return None, None

        trace_id = None
        if m := re.search(r"\"trace_id\"\s*:\s*\"(\w+)\"", message):
            trace_id = m.group(1)

        span_id = None
        if m := re.search(r"\"core_span_id\"\s*:\s*\"(\w+)\"", message):
            span_id = m.group(1)

        return trace_id, span_id

    except Exception:
        return None, None
