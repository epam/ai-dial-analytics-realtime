from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import aidial_analytics_realtime.app as app
from aidial_analytics_realtime.langid import LangID
from tests.mocks import InfluxWriterMock, TestTopicModel
from tests.utils.client import Client


@pytest.fixture(autouse=True)
def mock_uuid4():
    counter = 0

    def side_effect() -> str:
        nonlocal counter
        counter += 1
        return f"pseudo-uuid-{counter}"

    with patch(
        "aidial_analytics_realtime.analytics.uuid4", side_effect=side_effect
    ):
        yield


@pytest.fixture(scope="module")
def language_classifier():
    return LangID.create()


@pytest.fixture
def influx():
    return InfluxWriterMock()


@pytest.fixture
def topic_model():
    return TestTopicModel()


@pytest.fixture
def client(influx, language_classifier, topic_model) -> Client:
    app.app.dependency_overrides[app.LangID] = lambda: language_classifier
    app.app.dependency_overrides[app.InfluxWriterAsync] = lambda: influx  # type: ignore
    app.app.dependency_overrides[app.TopicModel] = lambda: topic_model
    return Client(
        http_client=TestClient(app.app, raise_server_exceptions=False)
    )
