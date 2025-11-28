import re
from typing import Any, List, Tuple

from pydantic import BaseModel


class DataRequest(BaseModel):
    __root__: List[Any]


class Message(BaseModel):
    message: str


_TRACE_IDS_RE = re.compile(r"\"(trace_id|core_span_id)\"\s*:\s*\"(\w+)\"")


def get_tracing_ids(request_message: Any) -> Tuple[str | None, str | None]:
    if not isinstance(request_message, dict):
        return None, None

    message = request_message.get("message")
    if not isinstance(message, str):
        return None, None

    # The message may be invalid JSON, therefore,
    # using regexp instead of trying to parse JSON.
    trace_id, span_id = None, None
    for name, value in _TRACE_IDS_RE.findall(message):
        if name == "trace_id":
            trace_id = value
        elif name == "core_span_id":
            span_id = value

    return trace_id, span_id
