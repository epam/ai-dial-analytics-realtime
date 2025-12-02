from typing import Dict

import pytest

from aidial_analytics_realtime.langid import LangID
from tests.mocks import InfluxWriterMock, TopicModelNoop
from tests.utils.client import Client
from tests.utils.influx import create_point
from tests.utils.message.chat import create_chat_message


@pytest.fixture(scope="module")
def language_classifier():
    return LangID.create()


@pytest.fixture
def topic_model():
    return TopicModelNoop()


_test_cases: Dict[str, str | None] = {
    "How are you doing? Do you speak english?": "en",
    "Longtemps, je me suis couché de bonne heure.": "fr",
    "qwerty-uiop": None,
}


@pytest.mark.with_external
@pytest.mark.parametrize("content, language", _test_cases.items())
def test_lang_id(
    client: Client, influx: InfluxWriterMock, content: str, language: str
):
    message = create_chat_message(
        request_body={"messages": [{"role": "user", "content": content}]}
    )
    client(message).raise_for_status()

    influx.match_points(
        create_point(topic=None, language=language, number_request_messages=1)
    )
