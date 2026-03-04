from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict

from .utils import parse_iso_datetime


class Mode(Enum):
    HOURLY = "hourly"
    MONTHLY = "monthly"


@dataclass
class Config:
    mode: Mode
    agg_database: str
    raw_table: str

    window_hours: int
    offset_minutes: int

    start_time: datetime | None
    end_time: datetime | None

    @classmethod
    def parse(cls, d: Dict[str, str] | None) -> "Config":
        d = d or {}

        mode_s = d.get("mode") or "hourly"
        try:
            mode = Mode(mode_s.strip().lower())
        except Exception as e:
            raise ValueError(f"Unsupported mode: {mode_s!r}") from e

        agg_database = d.get("agg_database")
        raw_table = d.get("raw_table")

        start_arg = d.get("start_time")
        end_arg = d.get("end_time")
        start_time: datetime | None = (
            parse_iso_datetime("start_time", start_arg) if start_arg else None
        )
        end_time: datetime | None = (
            parse_iso_datetime("end_time", end_arg) if end_arg else None
        )

        return cls(
            mode=mode,
            agg_database=agg_database or "analytics_agg",
            raw_table=raw_table or "analytics",
            start_time=start_time,
            end_time=end_time,
            window_hours=int(d.get("window_hours") or 6),
            offset_minutes=int(d.get("offset_minutes") or 2),
        )
