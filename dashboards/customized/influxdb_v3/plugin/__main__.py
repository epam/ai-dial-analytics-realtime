from __future__ import annotations

import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from . import process_scheduled_call
from .influx.mocks import MockInfluxDBClient


def main() -> None:
    if len(sys.argv) > 1:
        config_file = Path(sys.argv[1])
        args = tomllib.loads(Path(config_file).read_text())
    else:
        args = None

    # Only reads InfluxDB; doesn't write, so it's safe to use a local client for testing.
    process_scheduled_call(
        influxdb3_local=MockInfluxDBClient(),
        call_time=datetime.now(timezone.utc),
        args=args,
    )


if __name__ == "__main__":
    main()
