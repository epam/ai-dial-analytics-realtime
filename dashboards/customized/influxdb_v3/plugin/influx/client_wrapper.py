import json
from typing import Any, Dict, List

from ..utils.concurrency import Exec, SequentialExec
from .client_http import HTTPInfluxDBClient
from .types import InfluxDBClient, LineBuilderProtocol


class InfluxDBClientWrapper(InfluxDBClient):
    _log_prefix: str
    _database: str
    _verbose: bool
    _client: InfluxDBClient
    exec: Exec

    def __init__(
        self,
        *,
        client: InfluxDBClient,
        database: str,
        verbose: bool,
        exec: Exec | None = None,
        log_prefix: str = "",
    ):
        self._database = database
        self._log_prefix = log_prefix
        self._client = client
        self._verbose = verbose
        self.exec = exec or SequentialExec()

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
                f"SQL query returned {len(rows):>3} rows. First 3 are:\n{_prettify(prefix)}"
            )
        else:
            self.info(f"SQL query returned {len(rows):>3} rows.")

        return rows

    def write_to_db(self, db_name: str, line: LineBuilderProtocol) -> None:
        if self._verbose:
            self.info(f"Writing to database {db_name}: {line.build()}")
        else:
            self.info(f"Writing to database {db_name}...")

        self._client.write_to_db(db_name, line)

    def write_to_db_many(
        self, db_name: str, lines: List[LineBuilderProtocol]
    ) -> None:
        if not lines:
            return

        n = len(lines)
        if isinstance(self._client, HTTPInfluxDBClient):
            # TODO: missing info logs about the lines being written
            self._client.write_to_db(db_name, lines)
        else:
            for idx, line in enumerate(lines, start=1):
                prefix = f"[row|{idx:>2}/{n}]"
                self.add_prefix(prefix).write_to_db(db_name, line)

        self.info(f"wrote {n:>3} rows to {db_name}")

    def write_to_db_batched(
        self,
        db_name: str,
        lines: List[LineBuilderProtocol],
        *,
        batch_size: int,
    ) -> None:
        n = (len(lines) // batch_size) + bool(len(lines) % batch_size)
        for idx in range(1, n + 1):
            batch = lines[:batch_size]
            lines = lines[batch_size:]
            prefix = f"[batch|{idx:>2}/{n}]"
            self.add_prefix(prefix).write_to_db_many(db_name, batch)

    def info(self, msg: str) -> None:
        self._client.info(f"{self._log_prefix}[INFO] {msg}")

    def error(self, msg: str) -> None:
        self._client.error(f"{self._log_prefix}[ERROR] {msg}")


def _prettify(text: str) -> str:
    return _add_prefix_to_lines("    | ", text.strip())


def _add_prefix_to_lines(prefix: str, text: str) -> str:
    return "\n".join(prefix + line for line in text.splitlines())
