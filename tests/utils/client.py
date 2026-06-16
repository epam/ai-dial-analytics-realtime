import json
from typing import Any

import httpx2


class Client:
    http_client: httpx2.Client

    def __init__(self, http_client: httpx2.Client) -> None:
        self.http_client = http_client

    def post_json(self, payload: Any) -> httpx2.Response:
        return self.http_client.post(url="/data", json=payload)

    def __call__(self, *messages: dict) -> httpx2.Response:
        payload = [{"message": json.dumps(m)} for m in messages]
        return self.post_json(payload)
