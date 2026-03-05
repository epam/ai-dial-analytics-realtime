from __future__ import annotations

import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from . import process_scheduled_call
from .influx.mocks import MockInfluxDBClient


def main() -> None:
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.toml"
    config_file = Path(config_file)
    if not config_file.exists():
        args = {}
    else:
        args = tomllib.loads(Path(config_file).read_text())

    # Only reads InfluxDB; doesn't write, so it's safe to use a local client for testing.
    process_scheduled_call(
        influxdb3_local=MockInfluxDBClient(),
        call_time=datetime.now(timezone.utc),
        args=args,
    )


if __name__ == "__main__":
    main()
