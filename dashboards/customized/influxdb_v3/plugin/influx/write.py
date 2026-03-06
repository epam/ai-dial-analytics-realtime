import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from ..dates import parse_iso_date
from .client_http import HTTPInfluxDBClient
from .client_wrapper import InfluxDBClientWrapper
from .line_builder import LineBuilder as LineBuilderImpl
from .types import LineBuilderProtocol


def write_points(
    client: InfluxDBClientWrapper,
    *,
    db: str,
    table: str,
    rows: List[Dict[str, Any]],
    time_col: str,
    tag_cols: Tuple[str, ...],
    field_cols: Tuple[str, ...],
) -> int:
    """
    Write each row as a point into db_name.table_name.
    time_col can be ISO string, datetime, or ns int.
    """

    n = len(rows)
    for idx, row in enumerate(rows, start=1):
        builder = _create_data_point(
            _create_line_builder(client, table),
            row,
            time_col=time_col,
            tag_cols=tag_cols,
            field_cols=field_cols,
        )

        prefix = f"[point|{idx:>2}/{n}]"
        client.add_prefix(prefix).write_to_db(db, builder)

    client.info(f"wrote {n} points to {db}.{table}")
    return n


def _create_data_point(
    builder: LineBuilderProtocol,
    row: Dict[str, Any],
    *,
    time_col: str,
    tag_cols: Tuple[str, ...],
    field_cols: Tuple[str, ...],
) -> LineBuilderProtocol:
    r = row.copy()

    def r_json():
        return json.dumps(row)

    t = r.pop(time_col, None)
    if isinstance(t, str):
        builder.time_ns(_ns(parse_iso_date(f"{time_col!r} column", t)))
    else:
        raise ValueError(
            f"Unexpected time value in the column '{time_col!r}': {t} of type {type(t)}"
        )

    for k in tag_cols:
        if (v := r.pop(k, None)) is None:
            raise ValueError(
                f"Expected to find a tag column {k!r}, but it's missing from the given row: {r_json()}"
            )
        if isinstance(v, str):
            builder.tag(k, v)
        else:
            raise ValueError(
                f"Unexpected tag value in the column '{k!r}': {v} of type {type(v)}, but tags are expected to always be strings."
            )

    for k in field_cols:
        if (v := r.pop(k, None)) is None:
            raise ValueError(
                f"Expected to find a field column {k!r}, but it's missing from the given row: {r_json()}"
            )

        if isinstance(v, bool):
            builder.bool_field(k, v)
        elif isinstance(v, int):
            builder.int64_field(k, v)
        elif isinstance(v, float):
            builder.float64_field(k, v)
        else:
            raise ValueError(
                f"Unexpected field value in the column '{k!r}': {v} of type {type(v)}"
            )

    if r:
        raise ValueError(f"There are unhandled fields in the row: {r_json()}")

    return builder


def _ns(dt: datetime) -> int:
    return int(dt.astimezone(timezone.utc).timestamp() * 1_000_000_000)


def _create_line_builder(
    client: InfluxDBClientWrapper, table_name: str
) -> LineBuilderProtocol:
    if isinstance(client._client, HTTPInfluxDBClient):
        return LineBuilderImpl(table_name)
    else:
        # LineBuilder is available in the runtime:
        # https://docs.influxdata.com/influxdb3/enterprise/plugins/extend-plugin/#write-data
        # The actual LineBuilder code:
        # https://github.com/influxdata/influxdb/blob/37ff7e6cd4598c312df3688026764a322969c1de/influxdb3_py_api/src/system_py.rs#L508-L613
        return LineBuilder(table_name)  # type: ignore  # noqa: F821
