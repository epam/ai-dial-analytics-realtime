"""
{
  "plugin_type": [
    "scheduled"
  ],
  "scheduled_args_config": [
    {
      "name": "mode",
      "example": "6h",
      "description": "Which rollup to run: '6h' (default) or 'monthly'.",
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
      "description": "For mode=6h: window size in hours.",
      "required": false
    },
    {
      "name": "offset_minutes",
      "example": "2",
      "description": "For mode=6h: shift end of window backward to avoid late data.",
      "required": false
    },
    {
      "name": "start_time",
      "example": "2026-01-01T00:00:00Z",
      "description": "Optional backfill start (RFC3339). If set with end_time, overrides call_time-derived window.",
      "required": false
    },
    {
      "name": "end_time",
      "example": "2026-01-01T06:00:00Z",
      "description": "Optional backfill end (RFC3339). If set with start_time, overrides call_time-derived window.",
      "required": false
    }
  ]
}
"""

import uuid
from datetime import datetime, timezone

from .rollup_6h import run_6h
from .rollup_monthly import run_monthly


def process_scheduled_call(influxdb3_local, call_time: datetime, args=None):
    """
    InfluxDB 3 scheduled plugin entrypoint.
    """
    task_id = str(uuid.uuid4())
    args = args or {}

    call_time = call_time.replace(tzinfo=timezone.utc)
    mode = str(args.get("mode", "6h")).strip().lower()

    influxdb3_local.info(
        f"[{task_id}] scheduled call mode={mode} call_time={call_time.isoformat()} args={args}"
    )

    try:
        if mode == "monthly":
            run_monthly(influxdb3_local, call_time, args, task_id=task_id)
        elif mode == "6h":
            run_6h(influxdb3_local, call_time, args, task_id=task_id)
        else:
            raise ValueError(f"unsupported mode: {mode}")

        influxdb3_local.info(f"[{task_id}] completed OK")
    except Exception as e:
        influxdb3_local.error(f"[{task_id}] failed: {e}")
        raise
