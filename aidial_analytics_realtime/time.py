from datetime import UTC, datetime

import dateutil.parser as dateutil_parser


def parse_time(time_string: str) -> datetime:
    timestamp = dateutil_parser.isoparse(time_string)
    if timestamp.tzinfo is None:
        # The logs may come without the timezone information.
        # We want it to be interpreted as UTC, not local time.
        timestamp = timestamp.replace(tzinfo=UTC)
    return timestamp
