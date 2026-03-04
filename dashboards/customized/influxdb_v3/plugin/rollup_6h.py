from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from .utils import (
    parse_iso_datetime,
    query_rows,
    to_iso,
    token_class_case_sql,
    window_from_args_or_call_time,
    write_points,
)


def run_6h(
    influxdb3_local, call_time: datetime, args: Dict[str, Any], *, task_id: str
) -> None:
    raw_table = str(args.get("raw_table", "analytics"))
    agg_db = str(args.get("agg_database", "analytics_agg"))

    start_arg: str | None = args.get("start_time")
    end_arg: str | None = args.get("end_time")
    start_time: datetime | None = (
        parse_iso_datetime("start_time", start_arg) if start_arg else None
    )
    end_time: datetime | None = (
        parse_iso_datetime("end_time", end_arg) if end_arg else None
    )

    window_hours = int(args.get("window_hours") or 6)
    offset_minutes = int(args.get("offset_minutes") or 2)

    start, end = window_from_args_or_call_time(
        call_time,
        start_time,
        end_time,
        window_hours=window_hours,
        offset_minutes=offset_minutes,
    )

    start_s, end_s = to_iso(start), to_iso(end)

    influxdb3_local.info(f"[{task_id}] 6h rollup window: {start_s} .. {end_s}")

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
FROM {raw_table}
WHERE time >= '{start_s}' AND time < '{end_s}'
GROUP BY deployment, model, project_id, parent_deployment, language
"""
    stats_rows = query_rows(influxdb3_local, stats_sql)
    write_points(
        influxdb3_local,
        db_name=agg_db,
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

    # 2) default_agg_topic + default_agg_topic_2 (same content, but different retention/purpose - FIXME????)
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
FROM {raw_table}
WHERE time >= '{start_s}' AND time < '{end_s}'
GROUP BY title, topic, model
"""
    topic_rows = query_rows(influxdb3_local, topic_sql)

    for table in ("default_agg_topic", "default_agg_topic_2"):
        write_points(
            influxdb3_local,
            db_name=agg_db,
            table_name=table,
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

    # 3) token class histogram (kept compatible with your old task; stored in default_agg_topic by default)
    token_table = str(args.get("token_class_table", "default_agg_topic"))
    token_sql = f"""
SELECT
    '{start_s}' AS time,
    CASE
        WHEN user_hash = 'undefined'
        THEN 'project'
        ELSE 'user'
    END AS user_type,
    {token_class_case_sql()} AS prompt_token_class,
    COUNT(*) AS request_count
FROM {raw_table}
WHERE time >= '{start_s}' AND time < '{end_s}'
GROUP BY user_type, prompt_token_class
"""
    token_rows = query_rows(influxdb3_local, token_sql)
    write_points(
        influxdb3_local,
        db_name=agg_db,
        table_name=token_table,
        rows=token_rows,
        time_col="time",
        tag_cols=("user_type", "prompt_token_class"),
        field_cols=("request_count",),
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
FROM {raw_table}
WHERE time >= '{start_s}' AND time < '{end_s}'
GROUP BY user_hash, project_id, parent_deployment, title
"""
    kpi_rows = query_rows(influxdb3_local, kpi_sql)
    write_points(
        influxdb3_local,
        db_name=agg_db,
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
FROM {raw_table}
WHERE time >= '{start_s}' AND time < '{end_s}'
GROUP BY chat_id
"""
    chat_rows = query_rows(influxdb3_local, chat_sql)
    write_points(
        influxdb3_local,
        db_name=agg_db,
        table_name="default_agg_chatid",
        rows=chat_rows,
        time_col="time",
        tag_cols=("chat_id",),
        field_cols=("request_count",),
        task_id=task_id,
    )
