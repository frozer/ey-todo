import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

DEFAULT_BUCKET_SIZE = 10_000

@dataclass
class Decision:
  allowed: bool
  remaining: float
  retry_after: float      # seconds; 0 when allowed

class RateLimiter(ABC):
  @abstractmethod
  async def check(self, key: str, capacity: float, refill_rate_token_per_sec: float) -> Decision:
    """Try to consume 1 token from bucket `key`. Return the Decision."""


class InMemoryTokenBucket(RateLimiter):
  """Per-process token buckets; with N workers the effective limit is N x capacity."""

  def __init__(self, now: Callable[[], float] = time.monotonic, max_keys: int = DEFAULT_BUCKET_SIZE) -> None:
    self._now = now
    self._max_keys = max_keys
    # key -> (tokens, last_refill_ts, capacity, refill_rate)
    self._buckets: dict[str, tuple[float, float, float, float]] = {}

  async def check(self, key: str, capacity: float, refill_rate_token_per_sec: float) -> Decision:
    now = self._now()
    # first sight = full bucket
    tokens, ts, _, _ = self._buckets.get(key, (capacity, now, capacity, refill_rate_token_per_sec))

    elapsed = max(0, now - ts)
    tokens = min(capacity, tokens + elapsed * refill_rate_token_per_sec)
    allowed = tokens >= 1
    if allowed:
      tokens -= 1
    self._buckets[key] = (tokens, now, capacity, refill_rate_token_per_sec)
    if len(self._buckets) > self._max_keys:
      self._evict_full(now)
    retry_after = 0 if allowed else (1 - tokens) / refill_rate_token_per_sec
    return Decision(allowed, tokens, retry_after)

  def _evict_full(self, now: float) -> None:
    # a bucket that has refilled to capacity is indistinguishable from a fresh one
    self._buckets = {
      key: bucket
      for key, bucket in self._buckets.items()
      if bucket[0] + max(0, now - bucket[1]) * bucket[3] < bucket[2]
    }
