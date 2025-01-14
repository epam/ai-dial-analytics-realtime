class InfluxWriterMock:
    def __init__(self):
        self.points = []

    async def __call__(self, record):
        self.points.append(str(record))


class TestTopicModel:
    async def get_topic_by_text(self, text: str) -> str | None:
        return text or None
