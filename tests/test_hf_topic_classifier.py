import pytest

import aidial_analytics_realtime.app as app
from tests.mocks import InfluxWriterMock
from tests.utils.client import Client
from tests.utils.influx import create_chat_point
from tests.utils.message.chat import create_chat_message, create_chat_request


@pytest.fixture(scope="module")
def topic_model():
    return app.create_topic_model(topic_model="davanstrien/chat_topics")


_test_cases: dict[str, str] = {
    "let's play chess": "22_chess_chessboard_practice_strategy",
    "what's the third planet from Sun?": "31_planets_sun_earth_planet",
    "what's the best programming language?": "5_rust_haskell_programming_java",
}


@pytest.mark.with_external
@pytest.mark.parametrize("content, topic", _test_cases.items())
def test_topic_classification_by_hf_model(
    client: Client, influx: InfluxWriterMock, content: str, topic: str
):
    request_body = create_chat_request(
        messages=[{"role": "user", "content": content}]
    )
    message = create_chat_message(request_body=request_body)
    client(message).raise_for_status()
    influx.match_points(
        create_chat_point(topic=topic, number_request_messages=1)
    )
