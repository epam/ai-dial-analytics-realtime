import pytest
from fastapi.testclient import TestClient

import aidial_analytics_realtime.app as app
from aidial_analytics_realtime.langid import LangID
from tests.mocks import InfluxWriterMock


@pytest.fixture
def write_api_mock():
    return InfluxWriterMock()


@pytest.fixture(scope="module")
def language_classifier():
    return LangID.create()


@pytest.fixture
def client(write_api_mock, language_classifier, topic_model):
    app.app.dependency_overrides[app.LangID] = lambda: language_classifier
    app.app.dependency_overrides[app.InfluxWriterAsync] = lambda: write_api_mock
    app.app.dependency_overrides[app.TopicModel] = lambda: topic_model

    return TestClient(app.app, raise_server_exceptions=False)
