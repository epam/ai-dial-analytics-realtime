"""
{
    "plugin_type": [
        "scheduled"
    ],
    "scheduled_args_config": [
        {
            "name": "mode",
            "example": "hourly",
            "description": "Which rollup to run: 'hourly' (default) or 'monthly'.",
            "required": false
        },
        {
            "name": "raw_table",
            "example": "analytics",
            "description": "Raw source table name (in the trigger database).",
            "required": false
        },
        {
            "name": "agg_database",
            "example": "analytics_agg",
            "description": "Database to write aggregates into.",
            "required": false
        },
        {
            "name": "window_hours",
            "example": "6",
            "description": "For mode=hourly: window size in hours. Must be a divisor of 24. (default: 6 => windows are [00,06), [06,12), [12,18), [18,24)).",
            "required": false
        },
        {
            "name": "start_time",
            "example": "2026-01-01T00:00:00Z",
            "description": "Optional backfill start (ISO 8601). If set with end_time, overrides call_time-derived window.",
            "required": false
        },
        {
            "name": "end_time",
            "example": "2026-01-01T06:00:00Z",
            "description": "Optional backfill end (ISO 8601)). If set with start_time, overrides call_time-derived window.",
            "required": false
        }
    ]
}
"""

import sys
import tomllib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from typing_extensions import assert_never

from .config import Config, Mode
from .influx import InfluxDBClient
from .mocks import MockInfluxDBClient
from .rollup_hourly import run_hourly
from .rollup_monthly import run_monthly


def process_scheduled_call(
    influxdb3_local: InfluxDBClient,
    call_time: datetime,
    args: dict | None = None,
):
    """
    InfluxDB 3 scheduled plugin entrypoint.
    """
    task_id = str(uuid.uuid4())

    config = Config.parse(args)
    call_time = call_time.replace(tzinfo=timezone.utc)

    influxdb3_local.info(
        f"[{task_id}] scheduled call mode={config.mode} call_time={call_time.isoformat()} args={args}"
    )

    try:
        match config.mode:
            case Mode.MONTHLY:
                run_monthly(influxdb3_local, call_time, config, task_id=task_id)
            case Mode.HOURLY:
                run_hourly(influxdb3_local, call_time, config, task_id=task_id)
            case _:
                assert_never(config.mode)

        influxdb3_local.info(f"[{task_id}] completed OK")

    except Exception as e:
        influxdb3_local.error(f"[{task_id}] failed: {e}")
        raise


if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.toml"
    args = tomllib.loads(Path(config_file).read_text())

    # Only reads InfluxDB; doesn't write, so it's safe to use a local client for testing.
    process_scheduled_call(
        influxdb3_local=MockInfluxDBClient(),
        call_time=datetime.now(timezone.utc),
        args=args,
    )
