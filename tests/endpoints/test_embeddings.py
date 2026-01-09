import logging

import pytest

from tests.mocks import InfluxWriterMock
from tests.utils.client import Client
from tests.utils.influx import create_point
from tests.utils.message.embeddings import create_embedding_message


def test_embeddings_baseline(client: Client, influx: InfluxWriterMock):
    message = create_embedding_message()
    client(message).raise_for_status()

    point = create_point(
        response_id="pseudo-uuid-1",
        deployment="text-embedding-3-small",
        model="text-embedding-3-small",
    )

    influx.match_points(point)


def test_embeddings_no_request_body(client: Client, influx: InfluxWriterMock):
    message = create_embedding_message(request_body=None)
    client(message).raise_for_status()

    point = create_point(
        response_id="pseudo-uuid-1",
        deployment="text-embedding-3-small",
        model="text-embedding-3-small",
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
        number_request_messages=2,
    )

    influx.match_points(point)


def test_embeddings_trade_ids_in_log_messages(
    caplog, client: Client, influx: InfluxWriterMock
):
    caplog.set_level(logging.INFO)

    trace = {
        "trace_id": "5dca3d6ed5d22b6ab574f27a6ab5ec14",
        "core_span_id": "9ade2b6fef0a716d",
        "core_parent_span_id": "20e7e64715abbe97",
    }

    message = create_embedding_message(trace=trace)
    client(message).raise_for_status()

    point = create_point(
        response_id="pseudo-uuid-1",
        deployment="text-embedding-3-small",
        model="text-embedding-3-small",
        trace_id=trace["trace_id"],
        core_parent_span_id=trace["core_parent_span_id"],
        core_span_id=trace["core_span_id"],
    )

    influx.match_points(point)
    assert (
        f"[1/1] [trace_id={trace['trace_id']} span_id={trace["core_span_id"]}] success"
        in caplog.text
    )


@pytest.mark.parametrize(
    "request_uri, is_valid",
    [
        ("/openai/deployments/ID/embeddings", True),
        ("/openai/deployments/ID1/ID2/embeddings", True),
        ("/openai/deployments/ID/chat/embeddings/abc/efg", True),
        ("/openai/deployments/ID/embs", False),
        ("/openai/ID/embeddings", False),
    ],
)
def test_embeddings_request_uri(
    caplog,
    client: Client,
    influx: InfluxWriterMock,
    request_uri: str,
    is_valid: bool,
):
    message = create_embedding_message(request_uri=request_uri)
    response = client(message).raise_for_status()
    assert response.json() == [{"status": "success"}]

    if is_valid:
        influx.match_points(
            create_point(
                response_id="pseudo-uuid-1",
                deployment="text-embedding-3-small",
                model="text-embedding-3-small",
            )
        )
    else:
        influx.match_points()
        assert f"Unsupported message type: {request_uri!r}" in caplog.text
