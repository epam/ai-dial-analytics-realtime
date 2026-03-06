from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from .config import Config
from .influx.client_wrapper import InfluxDBClientWrapper
from .influx.write import write_points
from .window import Window


def run_hourly(
    client: InfluxDBClientWrapper, call_time: datetime, config: Config
) -> None:
    """
    Reads: raw_table
    Writes: default_agg_stats, default_agg_topic, default_agg_topic_2, default_agg_kpi, default_agg_chatid
    """

    windows = config.get_windows(call_time)

    n = len(windows)
    for idx, window in enumerate(windows, start=1):
        run_hourly_window(
            client.add_prefix(f"[win|{idx:>2}/{n}]"), config, window
        )


def run_hourly_window(
    client: InfluxDBClientWrapper, config: Config, window: Window
) -> None:
    client.info(
        f"{config.window_hours}-hours rollup window: {window.display()}"
    )

    start_s = window.start_s
    in_window = window.in_window_sql()

    # 1) default_agg_stats
    stats_sql = f"""
SELECT
    '{start_s}' AS time,
    deployment,
    model,
    project_id,
    parent_deployment,
    language,
    SUM(prompt_tokens)           AS prompt_tokens,
    SUM(completion_tokens)       AS completion_tokens,
    SUM(price)                   AS price,
    SUM(number_request_messages) AS number_request_messages,
    SUM(deployment_price)        AS deployment_price,
    COUNT(*)                     AS request_count,
    COUNT(DISTINCT user_hash)    AS unique_user_count
FROM {config.raw_table}
WHERE {in_window}
GROUP BY deployment, model, project_id, parent_deployment, language
"""

    stats_rows = client.query(stats_sql)
    write_points(
        client,
        db=config.agg_database,
        table="default_agg_stats",
        rows=_normalize_project_id(stats_rows),
        time_col="time",
        tag_cols=(
            "deployment",
            "model",
            "project_id",
            "parent_deployment",
            "language",
        ),
        field_cols=(
            "prompt_tokens",
            "completion_tokens",
            "price",
            "number_request_messages",
            "deployment_price",
            "request_count",
            "unique_user_count",
        ),
    )

    # 2) default_agg_topic_2
    topic_sql = f"""
SELECT
    '{start_s}' AS time,
    title,
    topic,
    model,
    COUNT(*)                      AS topic_count,
    SUM(number_request_messages)  AS number_request_messages,
    SUM(price)                    AS price,
    SUM(prompt_tokens)            AS prompt_tokens,
    SUM(completion_tokens)        AS completion_tokens
FROM {config.raw_table}
WHERE {in_window}
GROUP BY title, topic, model
"""

    topic_rows = client.query(topic_sql)
    write_points(
        client,
        db=config.agg_database,
        table="default_agg_topic_2",
        rows=_normalize_topic(topic_rows),
        time_col="time",
        tag_cols=("title", "topic", "model"),
        field_cols=(
            "topic_count",
            "number_request_messages",
            "price",
            "prompt_tokens",
            "completion_tokens",
        ),
    )

    # 3) default_agg_topic - token class histogram
    token_sql = f"""
SELECT
    '{start_s}' AS time,
    CASE
        WHEN user_hash = 'undefined'
        THEN 'project'
        ELSE 'user'
    END AS user_type,
    SUM(CAST(50000 <= prompt_tokens                           AS INT)) AS class_1,
    SUM(CAST(10000 <  prompt_tokens AND prompt_tokens < 50000 AS INT)) AS class_2,
    SUM(CAST( 5000 <  prompt_tokens AND prompt_tokens < 10000 AS INT)) AS class_3,
    SUM(CAST( 1000 <  prompt_tokens AND prompt_tokens <  5000 AS INT)) AS class_4,
    SUM(CAST(  100 <  prompt_tokens AND prompt_tokens <  1000 AS INT)) AS class_5,
    SUM(CAST(                           prompt_tokens <=  100 AS INT)) AS class_6
FROM {config.raw_table}
WHERE {in_window}
GROUP BY user_type
"""

    token_rows = client.query(token_sql)
    write_points(
        client,
        db=config.agg_database,
        table="default_agg_topic",
        rows=token_rows,
        time_col="time",
        tag_cols=("user_type",),
        field_cols=(
            "class_1",
            "class_2",
            "class_3",
            "class_4",
            "class_5",
            "class_6",
        ),
    )

    # 4) default_agg_kpi
    kpi_sql = f"""
SELECT
    '{start_s}' AS time,
    user_hash,
    project_id,
    parent_deployment,
    title,
    COUNT(*)               AS request_count,
    SUM(completion_tokens) AS completion_tokens,
    SUM(prompt_tokens)     AS prompt_tokens,
    SUM(price)             AS cost
FROM {config.raw_table}
WHERE {in_window}
GROUP BY user_hash, project_id, parent_deployment, title
"""

    kpi_rows = client.query(kpi_sql)
    write_points(
        client,
        db=config.agg_database,
        table="default_agg_kpi",
        rows=_normalize_project_id(kpi_rows),
        time_col="time",
        tag_cols=("user_hash", "project_id", "parent_deployment", "title"),
        field_cols=(
            "cost",
            "request_count",
            "completion_tokens",
            "prompt_tokens",
        ),
    )

    # 5) default_agg_chatid
    chat_sql = f"""
SELECT
    '{start_s}' AS time,
    chat_id,
    COUNT(*) AS request_count
FROM {config.raw_table}
WHERE {in_window}
GROUP BY chat_id
"""

    chat_rows = client.query(chat_sql)
    write_points(
        client,
        db=config.agg_database,
        table="default_agg_chatid",
        rows=chat_rows,
        time_col="time",
        tag_cols=("chat_id",),
        field_cols=("request_count",),
    )


def _normalize_project_id(rows: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    # Analytics may produce data points with missing (NULL) project_id field.
    # We are filling the gaps with a default to ease further processing of the data.
    for r in rows:
        if r.get("project_id") is None:
            r["project_id"] = "undefined"
    return rows


def _normalize_topic(rows: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    # Analytics may produce data points with missing (NULL) topic field.
    # We are filling the gaps with a default to ease further processing of the data.
    for r in rows:
        if r.get("topic") is None:
            r["topic"] = "undefined"
    return rows
