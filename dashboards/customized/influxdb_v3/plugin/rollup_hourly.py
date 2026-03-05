from __future__ import annotations

from datetime import datetime

from .config import Config
from .influx import query_rows, write_points
from .window import Window


def run_hourly(
    influxdb3_local, call_time: datetime, config: Config, *, task_id: str
) -> None:
    """
    Reads: raw_table
    Writes: default_agg_stats, default_agg_topic, default_agg_topic_2, default_agg_kpi, default_agg_chatid
    """

    windows = config.get_windows(call_time)

    for window in windows:
        run_hourly_window(influxdb3_local, config, window, task_id)


def run_hourly_window(
    influxdb3_local, config: Config, window: Window, task_id: str
) -> None:
    start_s = window.start_s
    in_window = window.in_window_sql()

    influxdb3_local.info(
        f"[{task_id}] {config.window_hours}-hours rollup window: {window.display()}"
    )

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

    stats_rows = query_rows(influxdb3_local, stats_sql)
    write_points(
        influxdb3_local,
        db_name=config.agg_database,
        table_name="default_agg_stats",
        rows=stats_rows,
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
        task_id=task_id,
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

    topic_rows = query_rows(influxdb3_local, topic_sql)
    write_points(
        influxdb3_local,
        db_name=config.agg_database,
        table_name="default_agg_topic_2",
        rows=topic_rows,
        time_col="time",
        tag_cols=("title", "topic", "model"),
        field_cols=(
            "topic_count",
            "number_request_messages",
            "price",
            "prompt_tokens",
            "completion_tokens",
        ),
        task_id=task_id,
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

    token_rows = query_rows(influxdb3_local, token_sql)
    write_points(
        influxdb3_local,
        db_name=config.agg_database,
        table_name="default_agg_topic",
        rows=token_rows,
        time_col="time",
        tag_cols=("user_type"),
        field_cols=(
            "class_1",
            "class_2",
            "class_3",
            "class_4",
            "class_5",
            "class_6",
        ),
        task_id=task_id,
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

    kpi_rows = query_rows(influxdb3_local, kpi_sql)
    write_points(
        influxdb3_local,
        db_name=config.agg_database,
        table_name="default_agg_kpi",
        rows=kpi_rows,
        time_col="time",
        tag_cols=("user_hash", "project_id", "parent_deployment", "title"),
        field_cols=(
            "cost",
            "request_count",
            "completion_tokens",
            "prompt_tokens",
        ),
        task_id=task_id,
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

    chat_rows = query_rows(influxdb3_local, chat_sql)
    write_points(
        influxdb3_local,
        db_name=config.agg_database,
        table_name="default_agg_chatid",
        rows=chat_rows,
        time_col="time",
        tag_cols=("chat_id",),
        field_cols=("request_count",),
        task_id=task_id,
    )
