from datetime import datetime, timedelta
from typing import List, Protocol

from .window import Window


class WindowRoller(Protocol):
    def align(self, call_time: datetime) -> datetime: ...
    def prev(self, time: datetime) -> datetime: ...


class HourlyRoller:
    def __init__(self, window_hours: int):
        if 24 % window_hours:
            raise ValueError("window_hours must divide 24 evenly")
        self.window_hours = window_hours

    def align(self, call_time: datetime) -> datetime:
        hour = call_time.hour - (call_time.hour % self.window_hours)
        return call_time.replace(hour=hour, minute=0, second=0, microsecond=0)

    def prev(self, time: datetime) -> datetime:
        return time - timedelta(hours=self.window_hours)


class MonthlyRoller:
    def align(self, call_time: datetime) -> datetime:
        return self._month_start(call_time)

    def prev(self, time: datetime) -> datetime:
        return self._month_start(time - timedelta(minutes=1))

    @staticmethod
    def _month_start(dt: datetime) -> datetime:
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def roll_windows(
    roller: WindowRoller, *, start_time: datetime | None, call_time: datetime
) -> List[Window]:

    end = roller.align(call_time)
    start = roller.prev(end)

    if start_time is None:
        return [Window(start=start, end=end)]

    ret: List[Window] = []
    while start_time <= start:
        ret.append(Window(start=start, end=end))
        end = start
        start = roller.prev(end)

    ret = ret[::-1]

    return ret
