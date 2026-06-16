import json
from typing import Any, Protocol


class HttpResponse(Protocol):
    status_code: int

    def json(self) -> Any: ...


class HttpClient(Protocol):
    def post(self, url: str, *, json: Any) -> HttpResponse: ...


class Client:
    http_client: HttpClient

    def __init__(self, http_client: HttpClient) -> None:
        self.http_client = http_client

    def post_json(self, payload: Any) -> HttpResponse:
        return self.http_client.post(url="/data", json=payload)

    def __call__(self, *messages: dict) -> HttpResponse:
        payload = [{"message": json.dumps(m)} for m in messages]
        return self.post_json(payload)
