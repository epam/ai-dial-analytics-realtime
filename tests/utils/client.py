import json
from typing import Any

import httpx


class Client:
    http_client: httpx.Client

    def __init__(self, http_client: httpx.Client) -> None:
        self.http_client = http_client

    def post_json(self, payload: Any) -> httpx.Response:
        return self.http_client.post(url="/data", json=payload)

    def __call__(self, *messages: dict) -> httpx.Response:
        payload = [{"message": json.dumps(m)} for m in messages]
        return self.post_json(payload)
