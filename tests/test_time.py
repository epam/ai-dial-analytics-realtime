from datetime import datetime, timedelta, timezone

import pytest

from aidial_analytics_realtime.time import parse_time


@pytest.mark.parametrize(
    "time_string, expected",
    [
        (
            "2011-12-03T10:15:30",
            datetime(2011, 12, 3, 10, 15, 30, tzinfo=timezone.utc),
        ),
        (
            "2011-12-03T10:15:30+01:00",
            datetime(
                2011, 12, 3, 10, 15, 30, tzinfo=timezone(timedelta(hours=1))
            ),
        ),
        (
            "2011-12-03T10:15:30.1",
            datetime(2011, 12, 3, 10, 15, 30, 100000, tzinfo=timezone.utc),
        ),
        (
            "2011-12-03T10:15:30.12",
            datetime(2011, 12, 3, 10, 15, 30, 120000, tzinfo=timezone.utc),
        ),
        (
            "2011-12-03T10:15:30.123",
            datetime(2011, 12, 3, 10, 15, 30, 123000, tzinfo=timezone.utc),
        ),
        (
            "2011-12-03T10:15:30.1234",
            datetime(2011, 12, 3, 10, 15, 30, 123400, tzinfo=timezone.utc),
        ),
        (
            "2011-12-03T10:15:30.12345",
            datetime(2011, 12, 3, 10, 15, 30, 123450, tzinfo=timezone.utc),
        ),
        (
            "2011-12-03T10:15:30.123456",
            datetime(2011, 12, 3, 10, 15, 30, 123456, tzinfo=timezone.utc),
        ),
        (
            "2011-12-03T10:15:30.1234567",
            datetime(2011, 12, 3, 10, 15, 30, 123456, tzinfo=timezone.utc),
        ),  # Python's datetime supports up to microsecond precision
    ],
)
def test_parse_time(time_string: str, expected: datetime):
    assert parse_time(time_string) == expected


@pytest.mark.parametrize(
    "time_string",
    [
        "2011-12-03T10:15:30.",  # No fractional part
        "2011-12-03T10:15:30+01:00[Europe/Paris]",  # Named timezones are not supported
    ],
)
def test_parse_time_should_fail(time_string: str):
    with pytest.raises(ValueError):
        parse_time(time_string)
