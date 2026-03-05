from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Sequence, Tuple

if TYPE_CHECKING:
    # LineBuilder is available in the processing runtime (as used by official plugins).
    # https://docs.influxdata.com/influxdb3/enterprise/plugins/extend-plugin/#write-data
    class LineBuilder:
        def __init__(self, measurement: str) -> None: ...
        def time_ns(self, value: int) -> None: ...
        def tag(self, key: str, value: str) -> None: ...
        def string_field(self, key: str, value: str) -> None: ...
        def int64_field(self, key: str, value: int) -> None: ...
        def float64_field(self, key: str, value: float) -> None: ...
        def bool_field(self, key: str, value: bool) -> None: ...


def parse_iso_datetime(name: str, value: str) -> datetime:
    try:
        # In Python<=3.10, "Z" was not supported by fromisoformat()
        dt: datetime = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(
            f"Invalid ISO 8601 datetime from the {name!r} column: {value!r}."
        )
    if dt.tzinfo is None:
        raise ValueError(
            f"Date from the {name!r} column must include timezone info (e.g., '+00:00'): {value!r}"
        )
    return dt.astimezone(timezone.utc)


def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ns(dt: datetime) -> int:
    return int(dt.astimezone(timezone.utc).timestamp() * 1_000_000_000)


def window_from_args_or_call_time(
    call_time: datetime,
    end_time: datetime | None,
    start_time: datetime | None,
    *,
    window_hours: int,
    offset_minutes: int,
) -> Tuple[datetime, datetime]:
    """
    If args contains start_time/end_time => backfill window.
    Else uses call_time to compute [end - window, end) with optional offset.
    """

    if start_time and end_time:
        if end_time <= start_time:
            raise ValueError(
                f"end_time must be > start_time (got {start_time} .. {end_time})"
            )
        return start_time, end_time

    end_time = call_time - timedelta(minutes=offset_minutes)
    start_time = end_time - timedelta(hours=window_hours)
    return start_time, end_time


def query_rows(influxdb3_local, sql: str) -> List[Dict[str, Any]]:
    """
    Execute SQL and return list of row dicts.
    """
    res = influxdb3_local.query(sql)
    return list(res) if res else []


def write_points(
    influxdb3_local,
    *,
    db_name: str,
    table_name: str,
    rows: Iterable[Dict[str, Any]],
    time_col: str,
    tag_cols: Sequence[str],
    field_cols: Sequence[str],
    task_id: str,
) -> int:
    """
    Write each row as a point into db_name.table_name.
    time_col can be RFC3339 string, datetime, or ns int.
    """
    written = 0

    for r in rows:
        b = LineBuilder(table_name)

        t = r.get(time_col)
        if isinstance(t, int):
            b.time_ns(t)
        elif isinstance(t, datetime):
            b.time_ns(_ns(t))
        elif isinstance(t, str):
            b.time_ns(_ns(parse_iso_datetime(f"{time_col!r} column", t)))
        else:
            raise ValueError(
                f"Unexpected time value in the column '{time_col!r}': {t} of type {type(t)}"
            )

        for k in tag_cols:
            if (v := r.get(k)) is not None:
                b.tag(k, str(v))

        for k in field_cols:
            if (v := r.get(k)) is not None:
                if isinstance(v, bool):
                    b.bool_field(k, v)
                elif isinstance(v, int):
                    b.int64_field(k, v)
                elif isinstance(v, float):
                    b.float64_field(k, v)
                else:
                    raise ValueError(
                        f"Unexpected field value in the column '{k!r}': {v} of type {type(v)}"
                    )

        influxdb3_local.write_to_db(db_name, b)
        written += 1

    influxdb3_local.info(
        f"[{task_id}] wrote {written} points -> {db_name}.{table_name}"
    )
    return written
