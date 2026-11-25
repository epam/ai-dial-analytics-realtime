from dataclasses import dataclass
from datetime import datetime

from .dates import to_iso_date


@dataclass
class Window:
    start: datetime
    end: datetime

    def display(self) -> str:
        return f"[{self.start_s} .. {self.end_s})"

    def in_window_sql(self) -> str:
        return f"'{self.start_s}' <= time AND time < '{self.end_s}'"

    @property
    def start_s(self) -> str:
        return to_iso_date(self.start)

    @property
    def end_s(self) -> str:
        return to_iso_date(self.end)
