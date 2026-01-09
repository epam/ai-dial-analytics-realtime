import pytest

from tests.mocks import InfluxWriterMock
from tests.utils.client import Client
from tests.utils.influx import create_rate_point
from tests.utils.message.base import on_request_body
from tests.utils.message.rate import create_rate_message


def test_rate_baseline(client: Client, influx: InfluxWriterMock):
    message = create_rate_message()
    client(message).raise_for_status()
    point = create_rate_point()
    influx.match_points(point)


def test_rate_deployment(client: Client, influx: InfluxWriterMock):
    message = create_rate_message(deployment="test-deployment-id")
    client(message).raise_for_status()
    point = create_rate_point(deployment="test-deployment-id")
    influx.match_points(point)


def test_rate_like(client: Client, influx: InfluxWriterMock):
    message = create_rate_message()

    def _set_like(body):
        body["rate"] = True

    client(message).raise_for_status()
    on_request_body(message, _set_like)

    point = create_rate_point(like_count=1, dislike_count=0)
    influx.match_points(point)


def test_rate_dislike(client: Client, influx: InfluxWriterMock):
    message = create_rate_message()

    def _set_dislike(body):
        body["rate"] = False

    on_request_body(message, _set_dislike)
    client(message).raise_for_status()

    point = create_rate_point(like_count=0, dislike_count=1)
    influx.match_points(point)


def test_rate_response_id(client: Client, influx: InfluxWriterMock):
    message = create_rate_message()

    def _set_dislike(body):
        body["responseId"] = "test-response-id"

    on_request_body(message, _set_dislike)
    client(message).raise_for_status()

    point = create_rate_point(response_id="test-response-id")
    influx.match_points(point)


def test_rate_tolerate_extra_fields(client: Client, influx: InfluxWriterMock):
    message = create_rate_message()

    def _set_extra(body):
        body["extra-field"] = "extra-field-value"

    on_request_body(message, _set_extra)
    client(message).raise_for_status()

    point = create_rate_point()
    influx.match_points(point)


@pytest.mark.parametrize(
    "request_uri, is_valid",
    [
        ("/v1/ID/rate", True),
        ("/v1/ID1/ID2/rate", True),
        ("/v1/ID/chat/rate/abc/efg", True),
        ("/v1/ID/rat", False),
        ("/ID/rate", False),
    ],
)
def test_rate_request_uri(
    caplog,
    client: Client,
    influx: InfluxWriterMock,
    request_uri: str,
    is_valid: bool,
):
    message = create_rate_message(request_uri=request_uri)
    response = client(message).raise_for_status()
    assert response.json() == [{"status": "success"}]

    if is_valid:
        influx.match_points(create_rate_point())
    else:
        influx.match_points()
        assert f"Unsupported message type: {request_uri!r}" in caplog.text
