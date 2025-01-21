class InfluxWriterMock:
    def __init__(self):
        self._points = []

    async def __call__(self, record):
        self._points.append(str(record))

    @property
    def points(self):
        return sorted(self._points)


class TestTopicModel:
    async def get_topic_by_text(self, text: str) -> str | None:
        return text or None
