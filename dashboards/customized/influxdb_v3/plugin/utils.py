from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Sequence, Tuple

if TYPE_CHECKING:
    # LineBuilder is available in the processing runtime (as used by official plugins).
    class LineBuilder:
        def __init__(self, measurement: str) -> None: ...
        def time_ns(self, value: int) -> None: ...
        def tag(self, key: str, value: str) -> None: ...
        def string_field(self, key: str, value: str) -> None: ...
        def int64_field(self, key: str, value: int) -> None: ...
        def float64_field(self, key: str, value: float) -> None: ...
        def bool_field(self, key: str, value: bool) -> None: ...


def parse_call_time(call_time: Any) -> datetime:
    """
    Best-effort conversion to a timezone-aware UTC datetime.
    """
    if isinstance(call_time, datetime):
        return (
            call_time
            if call_time.tzinfo
            else call_time.replace(tzinfo=timezone.utc)
        )

    if isinstance(call_time, str):
        s = call_time.strip()
        # Accept ...Z
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s).astimezone(timezone.utc)

    return datetime.now(tz=timezone.utc)


def parse_rfc3339(s: str) -> datetime:
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def rfc3339(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def ns(dt: datetime) -> int:
    return int(dt.astimezone(timezone.utc).timestamp() * 1_000_000_000)


def window_from_args_or_call_time(
    call_time: datetime,
    args: Dict[str, Any],
    *,
    window_hours_default: int = 6,
    offset_minutes_default: int = 2,
) -> Tuple[datetime, datetime]:
    """
    If args contains start_time/end_time => backfill window.
    Else uses call_time to compute [end - window, end) with optional offset.
    """
    start_arg = args.get("start_time")
    end_arg = args.get("end_time")

    if start_arg and end_arg:
        start = parse_rfc3339(str(start_arg))
        end = parse_rfc3339(str(end_arg))
        if end <= start:
            raise ValueError(
                f"end_time must be > start_time (got {start_arg} .. {end_arg})"
            )
        return start, end

    window_hours = int(args.get("window_hours", window_hours_default))
    offset_minutes = int(args.get("offset_minutes", offset_minutes_default))

    end = call_time - timedelta(minutes=offset_minutes)
    start = end - timedelta(hours=window_hours)
    return start, end


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
            b.time_ns(ns(t))
        elif isinstance(t, str):
            b.time_ns(ns(parse_rfc3339(t)))
        else:
            # fallback
            b.time_ns(ns(datetime.now(tz=timezone.utc)))

        for k in tag_cols:
            v = r.get(k)
            if v is None:
                continue
            # tags are always strings
            b.tag(k, str(v))

        for k in field_cols:
            v = r.get(k)
            if v is None:
                continue
            if isinstance(v, bool):
                b.bool_field(k, v)
            elif isinstance(v, int):
                b.int64_field(k, v)
            elif isinstance(v, float):
                b.float64_field(k, v)
            else:
                b.string_field(k, str(v))

        influxdb3_local.write_to_db(db_name, b)
        written += 1

    influxdb3_local.info(
        f"[{task_id}] wrote {written} points -> {db_name}.{table_name}"
    )
    return written


def token_class_case_sql() -> str:
    """
    Same thresholds/order as your Flux task.
    """
    return """
CASE
  WHEN prompt_tokens >= 50000 THEN 'class_1'
  WHEN prompt_tokens >  10000 THEN 'class_2'
  WHEN prompt_tokens >   5000 THEN 'class_3'
  WHEN prompt_tokens >   1000 THEN 'class_4'
  WHEN prompt_tokens >    100 THEN 'class_5'
  ELSE 'class_6'
END
""".strip()
