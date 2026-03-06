from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict

from .config import Config
from .influx.client_wrapper import InfluxDBClientWrapper
from .influx.write import write_points
from .window import Window


def run_monthly(
    client: InfluxDBClientWrapper, call_time: datetime, config: Config
) -> None:
    """
    Reads: default_agg_stats, default_agg_kpi
    Writes: default_agg_month
    """
    windows = config.get_windows(call_time)

    n = len(windows)
    for idx, window in enumerate(windows, start=1):
        run_monthly_window(
            client.add_prefix(f"[win|{idx}/{n}]"), config, window
        )


def run_monthly_window(
    client: InfluxDBClientWrapper, config: Config, window: Window
) -> None:
    client.info(f"monthly rollup window: {window.display()}")

    start_s = window.start_s
    in_window = window.in_window_sql()

    # API-level (project_id) rollups from default_agg_stats
    api_sql = f"""
SELECT
    '{start_s}' AS time,
    COALESCE(SUM(price),0)         AS total_cost_per_api,
    COALESCE(AVG(price),0)         AS avg_cost_per_api,
    COALESCE(SUM(request_count),0) AS total_rc_per_api,
    COALESCE(AVG(request_count),0) AS avg_rc_per_api,
    COUNT(*)                       AS active_apis
FROM ({_get_stats_sub_table("project_id", in_window)})
"""

    # Model-level rollups from default_agg_stats
    model_sql = f"""
SELECT
    '{start_s}' AS time,
    COALESCE(SUM(price),0) AS total_cost_per_model,
    COALESCE(AVG(price),0) AS avg_cost_per_model,
    COUNT(*)   AS active_models
FROM ({_get_stats_sub_table("model", in_window)})
"""

    # User-level rollups from default_agg_kpi
    user_sql = f"""
SELECT
    '{start_s}' AS time,
    COALESCE(SUM(cost),0) AS total_user_cost,
    COALESCE(AVG(cost),0) AS avg_cost_per_user,
    COUNT(*)  AS unique_users
FROM ({_get_kpi_sub_table(in_window)})
"""

    jobs = [
        lambda: client.add_prefix("[api  ]").query(api_sql),
        lambda: client.add_prefix("[model]").query(model_sql),
        lambda: client.add_prefix("[user ]").query(user_sql),
    ]

    results = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = [ex.submit(job) for job in jobs]
        for fut in as_completed(futures):
            results.append(fut.result())

    merged: Dict[str, Any] = {"time": start_s}
    for result in results:
        if result:
            merged.update(result[0])

    if (
        merged.get("unique_users", 0)
        + merged.get("active_apis", 0)
        + merged.get("active_models", 0)
        == 0
    ):
        client.info("No data. Skipping.")
        return

    merged.pop("active_models", None)

    write_points(
        client,
        db=config.agg_database,
        table="default_agg_month",
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
