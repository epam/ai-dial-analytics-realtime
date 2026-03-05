from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any, Dict, Iterable

from ..dates import parse_iso_date
from .mocks import create_line_builder
from .types import InfluxDBClient


def write_points(
    client: InfluxDBClient,
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
        b = create_line_builder(client, table_name)

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

        client.write_to_db(db_name, b)
        written += 1

    client.info(f"[{task_id}] wrote {written} points to {db_name}.{table_name}")
    return written


def _ns(dt: datetime) -> int:
    return int(dt.astimezone(timezone.utc).timestamp() * 1_000_000_000)
