import json
from typing import Any


def create_data_request(*messages: Any) -> Any:
    return [{"message": json.dumps(message)} for message in messages]
