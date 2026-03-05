from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List

from typing_extensions import assert_never

from .dates import parse_iso_date
from .window import Window
from .window_roller import HourlyRoller, MonthlyRoller, roll_windows


class Mode(Enum):
    HOURLY = "hourly"
    MONTHLY = "monthly"


@dataclass
class Config:
    mode: Mode
    agg_database: str
    raw_table: str

    window_hours: int

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

        agg_database = d.get("agg_database") or "analytics_agg"
        raw_table = d.get("raw_table") or "analytics"

        start_arg = d.get("start_time")
        end_arg = d.get("end_time")
        start_time: datetime | None = (
            parse_iso_date("start_time", start_arg) if start_arg else None
        )
        end_time: datetime | None = (
            parse_iso_date("end_time", end_arg) if end_arg else None
        )

        window_hours = int(d.get("window_hours") or 6)

        if 24 % window_hours:
            raise ValueError(
                f"window_hours must divide 24 evenly (got {window_hours})"
            )

        return cls(
            mode=mode,
            agg_database=agg_database,
            raw_table=raw_table,
            start_time=start_time,
            end_time=end_time,
            window_hours=window_hours,
        )

    def get_windows(self, call_time: datetime) -> List[Window]:
        call_time = call_time.astimezone(timezone.utc)
        if self.end_time:
            call_time = min(call_time, self.end_time)

        match self.mode:
            case Mode.HOURLY:
                roller = HourlyRoller(window_hours=self.window_hours)
            case Mode.MONTHLY:
                roller = MonthlyRoller()
            case _:
                assert_never(self.mode)

        return roll_windows(
            roller, start_time=self.start_time, call_time=call_time
        )
