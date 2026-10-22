from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, assert_never

from .utils.dates import parse_iso_date
from .utils.window import Window
from .utils.window_roller import HourlyRoller, MonthlyRoller, roll_windows


class Mode(Enum):
    HOURLY = "hourly"
    MONTHLY = "monthly"


@dataclass
class Config:
    mode: Mode
    agg_database: str

    raw_table: str  # used only in mode=hourly
    window_hours: int  # used only in mode=hourly

    start_time: datetime | None
    end_time: datetime | None

    verbose: bool

    @classmethod
    def parse(cls, d: Dict[str, str] | None) -> "Config":
        d = (d or {}).copy()

        mode_s = d.pop("mode", None) or "hourly"
        try:
            mode = Mode(mode_s.strip().lower())
        except Exception as e:
            raise ValueError(f"Unsupported mode: {mode_s!r}") from e

        agg_database = d.pop("agg_database", None) or "analytics_agg"
        raw_table = d.pop("raw_table", None) or "analytics"

        start_arg = d.pop("start_time", None)
        end_arg = d.pop("end_time", None)

        start_time: datetime | None = (
            parse_iso_date("start_time", start_arg) if start_arg else None
        )
        end_time: datetime | None = (
            parse_iso_date("end_time", end_arg) if end_arg else None
        )

        window_hours = int(d.pop("window_hours", None) or 6)
        if 24 % window_hours:
            raise ValueError(
                f"window_hours must divide 24 evenly (got {window_hours})"
            )

        verbose = (d.pop("verbose", None) or "false").lower() == "true"

        if d:
            raise ValueError(f"Unexpected config keys: {', '.join(d.keys())}")

        return cls(
            mode=mode,
            agg_database=agg_database,
            raw_table=raw_table,
            start_time=start_time,
            end_time=end_time,
            window_hours=window_hours,
            verbose=verbose,
        )

    @property
    def input_database(self) -> str:
        match self.mode:
            case Mode.HOURLY:
                return "default"
            case Mode.MONTHLY:
                return self.agg_database
            case _:
                assert_never(self.mode)

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
