class InfluxWriterMock:
    def __init__(self):
        self.points = []

    async def __call__(self, record):
        self.points.append(str(record))


class TestTopicModel:
    def get_topic_by_text(self, text):
        return text or None
