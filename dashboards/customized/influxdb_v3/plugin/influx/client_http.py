import json
from typing import Any, Dict, List
from urllib.request import Request, urlopen

from .types import InfluxDBClient, LineBuilderProtocol


class HTTPInfluxDBClient(InfluxDBClient):
    _influxdb_url: str
    _influxdb_token: str
    _database: str
    _readonly: bool

    def __init__(self, *, url: str, token: str, database: str, readonly: bool):
        self._database = database
        self._influxdb_url = url
        self._influxdb_token = token
        self._readonly = readonly

    def query(self, query: str) -> list[Dict[str, Any]]:
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

        return rows

    def write_to_db(
        self,
        db_name: str,
        line: LineBuilderProtocol | List[LineBuilderProtocol],
    ) -> None:
        if self._readonly:
            print("skipping writing...")
            return

        endpoint = f"{self._influxdb_url}/api/v3/write_lp?db={db_name}&precision=nanosecond&accept_partial=false&no_sync=false"

        lines = line if isinstance(line, list) else [line]
        data = "\n".join(line.build() for line in lines).encode()

        req = Request(
            endpoint,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Token {self._influxdb_token}",
                "Content-Type": "text/plain",
            },
        )

        with urlopen(req):
            # InfluxDB returns 204 on success.
            # We are not interested in the response.
            pass

    def info(self, msg: str) -> None:
        print(msg, flush=True)

    def error(self, msg: str) -> None:
        print(msg, flush=True)
