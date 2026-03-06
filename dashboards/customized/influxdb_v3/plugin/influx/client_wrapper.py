import json
from typing import Any, Dict

from .types import InfluxDBClient, LineBuilderProtocol


class InfluxDBClientWrapper(InfluxDBClient):
    _log_prefix: str
    _database: str
    _client: InfluxDBClient

    def __init__(
        self, *, client: InfluxDBClient, database: str, log_prefix: str = ""
    ):
        self._database = database
        self._log_prefix = log_prefix
        self._client = client

    def add_prefix(self, log_prefix: str) -> "InfluxDBClientWrapper":
        return InfluxDBClientWrapper(
            log_prefix=self._log_prefix + log_prefix,
            database=self._database,
            client=self._client,
        )

    def query(self, query: str) -> list[Dict[str, Any]]:
        print(f"{self._log_prefix}[QUERY REQUEST]\n{_prettify(query)}")

        rows = self._client.query(query)

        prefix = "\n".join(json.dumps(row) for row in rows[:3])
        print(
            f"{self._log_prefix}[QUERY RESULT](rows={len(rows)}):\n{_prettify(prefix)}"
        )

        return rows

    def write_to_db(self, db_name: str, line: LineBuilderProtocol) -> None:
        print(f"{self._log_prefix}[WRITE](db={db_name}) {line.build()}")
        self._client.write_to_db(db_name, line)

    def info(self, msg: str) -> None:
        self._client.info(f"{self._log_prefix}[INFO] {msg}")

    def error(self, msg: str) -> None:
        self._client.error(f"{self._log_prefix}[ERROR] {msg}")


def _prettify(text: str) -> str:
    return _line_prefix("    | ", text.strip())


def _line_prefix(prefix: str, text: str) -> str:
    return "\n".join(prefix + line for line in text.splitlines())
