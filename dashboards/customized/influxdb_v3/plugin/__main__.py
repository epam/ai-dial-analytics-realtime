from __future__ import annotations

import os
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from . import process_scheduled_call
from .config import Config
from .influx.mocks import HTTPInfluxDBClient


def _get_env(name: str) -> str:
    if (v := os.getenv(name)) is None:
        raise ValueError(f"Env variable {name!r} is unset")
    return v


def main() -> None:
    if len(sys.argv) > 1:
        config_file = Path(sys.argv[1])
        args = tomllib.loads(Path(config_file).read_text())
    else:
        args = {}

    readonly = args.pop("readonly", "false").lower() == "true"

    url = _get_env("INFLUX_URL")
    token = _get_env("INFLUX_API_TOKEN")

    database = Config.parse(args or {}).input_database
    client = HTTPInfluxDBClient(
        url=url, token=token, database=database, readonly=readonly
    )

    # Only reads InfluxDB; doesn't write, so it's safe to use a local client for testing.
    process_scheduled_call(
        influxdb3_local=client,
        call_time=datetime.now(timezone.utc),
        args=args,
    )


if __name__ == "__main__":
    main()
