from typing import List

from influxdb_client import Point


class InfluxWriterMock:
    _points: List[Point]

    def __init__(self):
        self._points = []

    async def __call__(self, record: Point):
        self._points.append(record)

    @property
    def points(self) -> List[str]:
        return sorted(map(str, self._points))

    @property
    def influx_points(self) -> List[Point]:
        return sorted(self._points, key=str)


class TestTopicModel:
    async def get_topic_by_text(self, text: str) -> str | None:
        return text or None
