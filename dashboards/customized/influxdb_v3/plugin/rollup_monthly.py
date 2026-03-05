from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from .config import Config
from .influx import InfluxDBClient, write_points
from .window import Window


def run_monthly(
    client: InfluxDBClient, call_time: datetime, config: Config, *, task_id: str
) -> None:
    """
    Reads: default_agg_stats, default_agg_kpi
    Writes: default_agg_month
    """
    windows = config.get_windows(call_time)

    for window in windows:
        run_monthly_window(client, config, window, task_id)


def run_monthly_window(
    client: InfluxDBClient, config: Config, window: Window, task_id: str
) -> None:
    start_s = window.start_s
    in_window = window.in_window_sql()

    client.info(f"[{task_id}] monthly rollup window: {window.display()}")

    # API-level (project_id) rollups from default_agg_stats
    api_sql = f"""
SELECT
    '{start_s}' AS time,
    SUM(price)         AS total_cost_per_api,
    AVG(price)         AS avg_cost_per_api,
    SUM(request_count) AS total_rc_per_api,
    AVG(request_count) AS avg_rc_per_api,
    COUNT(*)           AS active_apis
FROM ({_get_stats_sub_table("project_id", in_window)})
"""

    # Model-level rollups from default_agg_stats
    model_sql = f"""
SELECT
    '{start_s}' AS time,
    SUM(price) AS total_cost_per_model,
    AVG(price) AS avg_cost_per_model
FROM ({_get_stats_sub_table("model", in_window)})
"""

    # User-level rollups from default_agg_kpi
    user_sql = f"""
SELECT
    '{start_s}' AS time,
    SUM(cost) AS total_user_cost,
    AVG(cost) AS avg_cost_per_user,
    COUNT(*)  AS unique_users
FROM ({_get_kpi_sub_table(in_window)})
"""

    api_rows = client.query(api_sql)
    model_rows = client.query(model_sql)
    user_rows = client.query(user_sql)

    merged: Dict[str, Any] = {"time": start_s}
    if api_rows:
        merged.update(api_rows[0])
    if model_rows:
        merged.update(model_rows[0])
    if user_rows:
        merged.update(user_rows[0])

    write_points(
        client,
        db_name=config.agg_database,
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


def _get_stats_sub_table(group_by: str, in_window: str) -> str:
    return f"""
SELECT
    SUM(price)         AS price,
    SUM(request_count) AS request_count
FROM default_agg_stats
WHERE {in_window}
    AND project_id IS NOT NULL
    AND project_id <> ''
GROUP BY {group_by}
""".strip()


def _get_kpi_sub_table(in_window: str) -> str:
    return f"""
SELECT
    SUM(cost) AS cost
FROM default_agg_kpi
WHERE {in_window}
    AND user_hash IS NOT NULL
    AND user_hash <> 'undefined'
GROUP BY user_hash
""".strip()
