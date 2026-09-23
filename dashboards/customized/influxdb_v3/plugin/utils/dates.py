from datetime import datetime, timezone


def parse_iso_date(name: str, value: str) -> datetime:
    try:
        # In Python<=3.10, "Z" was not supported by fromisoformat()
        dt: datetime = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(
            f"Invalid ISO 8601 datetime from the {name!r} column: {value!r}."
        )
    if dt.tzinfo is None:
        raise ValueError(
            f"Date from the {name!r} column must include timezone info (e.g., '+00:00'): {value!r}"
        )
    return dt.astimezone(timezone.utc)


def to_iso_date(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
