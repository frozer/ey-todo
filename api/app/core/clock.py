from collections.abc import Callable
from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)

def get_clock() -> Callable[[], datetime]:
    """The clock for every auth decision. Tests override it to freeze time."""
    return utc_now

def is_past(stamp: datetime, now: datetime) -> bool:
  return stamp < now