class InfluxWriterMock:
    def __init__(self):
        self.points = []

    async def __call__(self, record):
        self.points.append(str(record))
