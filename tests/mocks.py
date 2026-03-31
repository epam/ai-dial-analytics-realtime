from functools import cached_property
from typing import List

from influxdb_client import Point


class InfluxWriterMock:
    _points: List[Point]

    def __init__(self):
        self._points = []

    async def __call__(self, record: Point):
        self._points.append(record)

    @cached_property
    def points(self) -> List[str]:
        return sorted(map(str, self._points))

    @cached_property
    def influx_points(self) -> List[Point]:
        return sorted(self._points, key=str)

    def match_points(self, *expected_points: Point):
        assert len(expected_points) == len(self.points)
        expected_strings = sorted(expected_points, key=str)
        for expected, actual in zip(
            expected_strings, self.influx_points, strict=False
        ):
            assert str(expected) == str(actual)


class LangIDNotImplemented:
    async def detect_language(self, text: str) -> str | None:
        raise NotImplementedError("LangID isn't implemented")


class LangIDNoop:
    async def detect_language(self, text: str) -> str | None:
        return None


class TopicModelEcho:
    async def get_topic_by_text(self, text: str) -> str | None:
        return text or None


class TopicModelNoop:
    async def get_topic_by_text(self, text: str) -> str | None:
        return None


class TopicModelNotImplemented:
    async def get_topic_by_text(self, text: str) -> str | None:
        raise NotImplementedError("TopicModel isn't implemented")
