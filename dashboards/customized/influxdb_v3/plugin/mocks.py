from typing import Any, Dict

from .influx import InfluxDBClient, LineBuilderProtocol


class MockInfluxDBClient(InfluxDBClient):
    def query(self, query: str) -> list[Dict[str, Any]]:
        print(f"MockInfluxDBClient.query:\n{query}\n")
        return []

    def write_to_db(self, db_name: str, line: LineBuilderProtocol) -> None:
        print(
            f"MockInfluxDBClient.write_to_db:\ndb_name={db_name}\nline={line.build()}"
        )

    def info(self, msg: str) -> None:
        print(f"INFO: {msg}")

    def error(self, msg: str) -> None:
        print(f"ERROR: {msg}")


class MockLineBuilder(LineBuilderProtocol):
    _measurement: str
    _time: int
    _tags: Dict[str, str]
    _fields: Dict[str, Any]

    def __init__(self, measurement: str) -> None:
        self._measurement = measurement
        self._time = 0
        self._tags = {}
        self._fields = {}

    def time_ns(self, value: int) -> None:
        self._time = value

    def tag(self, key: str, value: str) -> None:
        self._tags[key] = value

    def string_field(self, key: str, value: str) -> None:
        self._fields[key] = value

    def int64_field(self, key: str, value: int) -> None:
        self._fields[key] = value

    def float64_field(self, key: str, value: float) -> None:
        self._fields[key] = value

    def bool_field(self, key: str, value: bool) -> None:
        self._fields[key] = value

    def build(self) -> str:
        return f"MockLine(measurement={self._measurement!r}, time_ns={self._time}, tags={self._tags}, fields={self._fields})"


def create_line_builder(
    client: InfluxDBClient, table_name: str
) -> LineBuilderProtocol:
    if isinstance(client, MockInfluxDBClient):
        return MockLineBuilder(table_name)
    else:
        # LineBuilder is available in the runtime:
        # https://docs.influxdata.com/influxdb3/enterprise/plugins/extend-plugin/#write-data
        # The actual LineBuilder code:
        # https://github.com/influxdata/influxdb/blob/37ff7e6cd4598c312df3688026764a322969c1de/influxdb3_py_api/src/system_py.rs#L508-L613
        return LineBuilder(table_name)  # type: ignore  # noqa: F821
