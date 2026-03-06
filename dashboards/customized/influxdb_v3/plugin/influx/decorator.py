import json
from typing import Any, Dict

from .types import InfluxDBClient, LineBuilderProtocol


class LoggingDecorator(InfluxDBClient):
    _task_id: str
    _database: str
    _client: InfluxDBClient

    def __init__(self, *, task_id: str, database: str, client: InfluxDBClient):
        self._database = database
        self._task_id = task_id
        self._client = client

    def query(self, query: str) -> list[Dict[str, Any]]:
        print(f"[{self._task_id}][QUERY REQUEST]\n{_prettify(query)}")

        rows = self._client.query(query)

        prefix = "\n".join(json.dumps(row) for row in rows[:3])
        print(
            f"[{self._task_id}][QUERY RESULT](rows={len(rows)}):\n{_prettify(prefix)}"
        )

        return rows

    def write_to_db(self, db_name: str, line: LineBuilderProtocol) -> None:
        print(f"[{self._task_id}][WRITE](db={db_name}) {line.build()}")
        self._client.write_to_db(db_name, line)

    def info(self, msg: str) -> None:
        self._client.info(f"[{self._task_id}][INFO] {msg}")

    def error(self, msg: str) -> None:
        self._client.error(f"[{self._task_id}][ERROR] {msg}")


def _prettify(text: str) -> str:
    return _line_prefix("    | ", text.strip())


def _line_prefix(prefix: str, text: str) -> str:
    return "\n".join(prefix + line for line in text.splitlines())
