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

    def match_points(self, *points: Point):
        assert len(points) == len(self.points)
        sorted_points = sorted(list(points), key=str)
        for expected, actual in zip(sorted_points, self.influx_points):
            assert str(expected) == str(actual)


class TestTopicModel:
    async def get_topic_by_text(self, text: str) -> str | None:
        return text or None
