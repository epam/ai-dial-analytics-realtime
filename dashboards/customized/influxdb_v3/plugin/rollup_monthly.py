from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from .utils import query_rows, rfc3339, write_points


def _month_start(dt: datetime) -> datetime:
    dt = dt.astimezone(timezone.utc)
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def run_monthly(
    influxdb3_local, call_time: datetime, args: Dict[str, Any], *, task_id: str
) -> None:
    agg_db = str(args.get("agg_database", "analytics_agg"))

    # Previous month window: [prev_month_start, this_month_start)
    this_month = _month_start(call_time)
    prev_month = _month_start(this_month - timedelta(days=32))

    start_s = rfc3339(prev_month)
    end_s = rfc3339(this_month)
    stamp_s = start_s  # stamp results at first day of prev month

    influxdb3_local.info(
        f"[{task_id}] monthly rollup window: {start_s} .. {end_s}"
    )

    # API-level (project_id) rollups from default_agg_stats
    api_sql = f"""
SELECT
  '{stamp_s}' AS time,
  SUM(price)                 AS total_cost_per_api,
  AVG(price)                 AS avg_cost_per_api,
  COUNT(DISTINCT project_id) AS active_apis,
  SUM(request_count)         AS total_rc_per_api,
  AVG(request_count)         AS avg_rc_per_api
FROM default_agg_stats
WHERE time >= '{start_s}' AND time < '{end_s}'
  AND project_id IS NOT NULL AND project_id <> ''
"""
    api_rows = query_rows(influxdb3_local, api_sql)

    # Model-level rollups from default_agg_stats
    model_sql = f"""
SELECT
  '{stamp_s}' AS time,
  SUM(price) AS total_cost_per_model,
  AVG(price) AS avg_cost_per_model
FROM default_agg_stats
WHERE time >= '{start_s}' AND time < '{end_s}'
"""
    model_rows = query_rows(influxdb3_local, model_sql)

    # User-level rollups from default_agg_kpi (exclude undefined like your Flux)
    user_sql = f"""
SELECT
  '{stamp_s}' AS time,
  SUM(cost)                 AS total_user_cost,
  AVG(cost)                 AS avg_cost_per_user,
  COUNT(DISTINCT user_hash) AS unique_users
FROM default_agg_kpi
WHERE time >= '{start_s}' AND time < '{end_s}'
  AND user_hash IS NOT NULL AND user_hash <> 'undefined'
"""
    user_rows = query_rows(influxdb3_local, user_sql)

    merged: Dict[str, Any] = {"time": stamp_s}
    if api_rows:
        merged.update(api_rows[0])
    if model_rows:
        merged.update(model_rows[0])
    if user_rows:
        merged.update(user_rows[0])

    write_points(
        influxdb3_local,
        db_name=agg_db,
        table_name="default_agg_month",
        rows=[merged],
        time_col="time",
        tag_cols=(),
        field_cols=(
            "total_user_cost",
            "avg_cost_per_user",
            "unique_users",
            "total_cost_per_api",
            "avg_cost_per_api",
            "active_apis",
            "total_rc_per_api",
            "avg_rc_per_api",
            "total_cost_per_model",
            "avg_cost_per_model",
        ),
        task_id=task_id,
    )
