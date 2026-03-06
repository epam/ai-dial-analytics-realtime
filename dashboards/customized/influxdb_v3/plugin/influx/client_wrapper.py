import json
from typing import Any, Dict

from .types import InfluxDBClient, LineBuilderProtocol


class InfluxDBClientWrapper(InfluxDBClient):
    _log_prefix: str
    _database: str
    _verbose: bool
    _client: InfluxDBClient

    def __init__(
        self,
        *,
        client: InfluxDBClient,
        database: str,
        verbose: bool,
        log_prefix: str = "",
    ):
        self._database = database
        self._log_prefix = log_prefix
        self._client = client
        self._verbose = verbose

    def add_prefix(self, log_prefix: str) -> "InfluxDBClientWrapper":
        return InfluxDBClientWrapper(
            log_prefix=self._log_prefix + log_prefix,
            verbose=self._verbose,
            database=self._database,
            client=self._client,
        )

    def query(self, query: str) -> list[Dict[str, Any]]:
        if self._verbose:
            self.info(f"SQL query:\n{_prettify(query)}")

        rows = self._client.query(query)

        if self._verbose:
            prefix = "\n".join(json.dumps(row) for row in rows[:3])
            self.info(
                f"SQL query returned {len(rows)} rows. First 3 are:\n{_prettify(prefix)}"
            )
        else:
            self.info(f"SQL query returned {len(rows)} rows.")

        return rows

    def write_to_db(self, db_name: str, line: LineBuilderProtocol) -> None:
        if self._verbose:
            self.info(f"Writing to database {db_name}: {line.build()}")
        else:
            self.info(f"Writing to database {db_name}...")

        self._client.write_to_db(db_name, line)

    def info(self, msg: str) -> None:
        self._client.info(f"{self._log_prefix}[INFO] {msg}")

    def error(self, msg: str) -> None:
        self._client.error(f"{self._log_prefix}[ERROR] {msg}")


def _prettify(text: str) -> str:
    return _add_prefix_to_lines("    | ", text.strip())


def _add_prefix_to_lines(prefix: str, text: str) -> str:
    return "\n".join(prefix + line for line in text.splitlines())
