from tests.mocks import InfluxWriterMock
from tests.utils.client import Client
from tests.utils.influx import create_point
from tests.utils.message import create_embedding_message


def test_embeddings_baseline(client: Client, influx: InfluxWriterMock):
    message = create_embedding_message()
    client(message).raise_for_status()

    point = create_point(
        response_id="pseudo-uuid-1",
        deployment="text-embedding-3-small",
        model="text-embedding-3-small",
        topic="fish\n\ncat",
    )

    influx.match_points(point)


def test_embeddings_no_request_body(client: Client, influx: InfluxWriterMock):
    message = create_embedding_message(request_body=None)
    client(message).raise_for_status()

    point = create_point(
        response_id="pseudo-uuid-1",
        deployment="text-embedding-3-small",
        model="text-embedding-3-small",
        topic="undefined",
        number_request_messages=0,
    )

    influx.match_points(point)


def test_embeddings_input_as_tokens(client: Client, influx: InfluxWriterMock):
    message = create_embedding_message(
        request_body={"input": [[1, 3, 4, 5], [6, 7, 8, 9]]}
    )
    client(message).raise_for_status()

    point = create_point(
        response_id="pseudo-uuid-1",
        deployment="text-embedding-3-small",
        model="text-embedding-3-small",
        topic="undefined",
        number_request_messages=2,
    )

    influx.match_points(point)
