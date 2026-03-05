import json
from typing import Any, Dict
from urllib.request import Request, urlopen

from .types import InfluxDBClient, LineBuilderProtocol


class DryRunInfluxDBClient(InfluxDBClient):
    _influxdb_url: str
    _influxdb_token: str

    _database: str

    def __init__(self, *, url: str, token: str, database: str):
        self._database = database
        self._influxdb_url = url
        self._influxdb_token = token

    def query(self, query: str) -> list[Dict[str, Any]]:
        query = query.strip()
        print(f"[INFLUX QUERY]\n{_line_prefix("    | ", query)}")

        endpoint = f"{self._influxdb_url}/api/v3/query_sql"

        payload = json.dumps(
            {"formats": "json", "db": self._database, "q": query}
        ).encode("utf-8")

        req = Request(
            endpoint,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Token {self._influxdb_token}",
                "Content-Type": "application/json",
            },
        )

        with urlopen(req) as resp:
            rows = json.load(resp)

        prefix = json.dumps(rows[:3], indent=2)
        prefix = _line_prefix("    | ", prefix.strip())
        print(f"[INFLUX QUERY RESPONSE](rows={len(rows)}):\n{prefix}")

        return rows

    def write_to_db(self, db_name: str, line: LineBuilderProtocol) -> None:
        print(f"[INFLUX WRITE](db_name={db_name})\n{line.build()}")

    def info(self, msg: str) -> None:
        print(f"[PLUGIN INFO] {msg}")

    def error(self, msg: str) -> None:
        print(f"[PLUGIN ERROR] {msg}")


def _line_prefix(prefix: str, text: str) -> str:
    return "\n".join(prefix + line for line in text.splitlines())


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
    if isinstance(client, DryRunInfluxDBClient):
        return MockLineBuilder(table_name)
    else:
        # LineBuilder is available in the runtime:
        # https://docs.influxdata.com/influxdb3/enterprise/plugins/extend-plugin/#write-data
        # The actual LineBuilder code:
        # https://github.com/influxdata/influxdb/blob/37ff7e6cd4598c312df3688026764a322969c1de/influxdb3_py_api/src/system_py.rs#L508-L613
        return LineBuilder(table_name)  # type: ignore  # noqa: F821
