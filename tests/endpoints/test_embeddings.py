from tests.mocks import InfluxWriterMock
from tests.utils.client import Client
from tests.utils.influx import create_point
from tests.utils.message import create_message


def test_embeddings_input_as_text(client: Client, influx: InfluxWriterMock):
    message = create_message(
        deployment="text-embedding-3-small",
        request_uri="/openai/deployments/text-embedding-3-small/embeddings?api-version=2023-03-15-preview",
        request_body={"input": ["fish", "cat"]},
        response_body={
            "object": "list",
            "model": "text-embedding-3-small",
            "data": [
                {"index": 0, "object": "embedding", "embedding": [0.1, 0.2]},
                {"index": 1, "object": "embedding", "embedding": [0.3, 0.4]},
            ],
            "usage": {"prompt_tokens": 43, "total_tokens": 43},
        },
    )

    client(message).raise_for_status()

    point = create_point(
        response_id="pseudo-uuid-1",
        deployment="text-embedding-3-small",
        model="text-embedding-3-small",
        topic="fish\n\ncat",
    )

    influx.match_points(point)


def test_embeddings_no_request_body(client: Client, influx: InfluxWriterMock):
    message = create_message(
        deployment="text-embedding-3-small",
        request_uri="/openai/deployments/text-embedding-3-small/embeddings?api-version=2023-03-15-preview",
        request_body=None,
        response_body={
            "object": "list",
            "model": "text-embedding-3-small",
            "data": [
                {"index": 0, "object": "embedding", "embedding": [0.1, 0.2]},
                {"index": 1, "object": "embedding", "embedding": [0.3, 0.4]},
            ],
            "usage": {"prompt_tokens": 43, "total_tokens": 43},
        },
    )

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
    message = create_message(
        deployment="text-embedding-3-small",
        request_uri="/openai/deployments/text-embedding-3-small/embeddings?api-version=2023-03-15-preview",
        request_body={"input": [[1, 3, 4, 5], [6, 7, 8, 9]]},
        response_body={
            "object": "list",
            "model": "text-embedding-3-small",
            "data": [
                {"index": 0, "object": "embedding", "embedding": [0.1, 0.2]},
                {"index": 1, "object": "embedding", "embedding": [0.3, 0.4]},
            ],
            "usage": {"prompt_tokens": 43, "total_tokens": 43},
        },
    )

    client(message).raise_for_status()

    point = create_point(
        response_id="pseudo-uuid-1",
        deployment="text-embedding-3-small",
        model="text-embedding-3-small",
        topic="undefined",
    )

    influx.match_points(point)
