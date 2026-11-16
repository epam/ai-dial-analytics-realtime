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
        {
            "name": "verbose",
            "example": "true",
            "description": "Enable verbose logging including SQL queries and data points written to InfluxDB. False by default.",
            "required": false
        }
    ]
}
"""

import uuid
from datetime import datetime, timezone
from typing import assert_never

from .config import Config, Mode
from .influx.client_wrapper import InfluxDBClientWrapper
from .influx.types import InfluxDBClient
from .rollup_hourly import run_hourly
from .rollup_monthly import run_monthly
from .utils.concurrency import Exec


def process_scheduled_call(
    influxdb3_local: InfluxDBClient,
    call_time: datetime,
    args: dict | None = None,
    exec: Exec | None = None,
):
    """
    InfluxDB 3 scheduled plugin entrypoint.
    """
    config = Config.parse(args)
    call_time = call_time.replace(tzinfo=timezone.utc)

    client = InfluxDBClientWrapper(
        client=influxdb3_local,
        exec=exec,
        database=config.input_database,
        verbose=config.verbose,
    ).add_prefix(f"[{str(uuid.uuid4())}]")

    client.info(
        f"scheduled call mode={config.mode.value} call_time={call_time.isoformat()} args={args}"
    )

    try:
        match config.mode:
            case Mode.MONTHLY:
                run_monthly(client, call_time, config)
            case Mode.HOURLY:
                run_hourly(client, call_time, config)
            case _:
                assert_never(config.mode)

        client.info("completed OK")

    except Exception as e:
        client.error(f"failed: {e}")
        raise
