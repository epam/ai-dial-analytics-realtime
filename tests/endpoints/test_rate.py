from tests.mocks import InfluxWriterMock
from tests.utils.client import Client
from tests.utils.influx import create_rate_point
from tests.utils.message import create_rate_message, on_request_body


def test_rate_request_baseline(client: Client, influx: InfluxWriterMock):
    message = create_rate_message()
    client(message).raise_for_status()
    point = create_rate_point()
    influx.match_points(point)


def test_rate_request_like(client: Client, influx: InfluxWriterMock):
    message = create_rate_message()

    def _set_like(body):
        body["rate"] = True

    client(message).raise_for_status()
    on_request_body(message, _set_like)

    point = create_rate_point(like_count=1, dislike_count=0)
    influx.match_points(point)


def test_rate_request_dislike(client: Client, influx: InfluxWriterMock):
    message = create_rate_message()

    def _set_dislike(body):
        body["rate"] = False

    on_request_body(message, _set_dislike)
    client(message).raise_for_status()

    point = create_rate_point(like_count=0, dislike_count=1)
    influx.match_points(point)


def test_rate_request_response_id(client: Client, influx: InfluxWriterMock):
    message = create_rate_message()

    def _set_dislike(body):
        body["responseId"] = "test-response-id"

    on_request_body(message, _set_dislike)
    client(message).raise_for_status()

    point = create_rate_point(response_id="test-response-id")
    influx.match_points(point)


def test_rate_request_tolerate_extra_fields(
    client: Client, influx: InfluxWriterMock
):
    message = create_rate_message()

    def _set_extra(body):
        body["extra-field"] = "extra-field-value"

    on_request_body(message, _set_extra)
    client(message).raise_for_status()

    point = create_rate_point()
    influx.match_points(point)
