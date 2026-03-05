import json
from typing import Any, Dict
from urllib.request import Request, urlopen

from .types import InfluxDBClient, LineBuilderProtocol


class ReadOnlyInfluxDBClient(InfluxDBClient):
    _influxdb_url: str
    _influxdb_token: str

    _database: str

    def __init__(self, *, url: str, token: str, database: str):
        self._database = database
        self._influxdb_url = url
        self._influxdb_token = token

    def query(self, query: str) -> list[Dict[str, Any]]:
        print(f"[INFLUX QUERY]\n{_prettify(query)}")

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
        print(
            f"[INFLUX QUERY RESPONSE](rows={len(rows)}):\n{_prettify(prefix)}"
        )

        return rows

    def write_to_db(self, db_name: str, line: LineBuilderProtocol) -> None:
        print(f"[INFLUX WRITE](db_name={db_name})\n{line.build()}")

    def info(self, msg: str) -> None:
        print(f"[PLUGIN INFO] {msg}")

    def error(self, msg: str) -> None:
        print(f"[PLUGIN ERROR] {msg}")


def _prettify(text: str) -> str:
    return _line_prefix("    | ", text.strip())


def _line_prefix(prefix: str, text: str) -> str:
    return "\n".join(prefix + line for line in text.splitlines())
