from collections.abc import Sequence
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Iterable, List

from .utils import parse_iso_date

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
            b.time_ns(_ns(parse_iso_date(f"{time_col!r} column", t)))
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


def _ns(dt: datetime) -> int:
    return int(dt.astimezone(timezone.utc).timestamp() * 1_000_000_000)
