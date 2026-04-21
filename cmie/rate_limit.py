from __future__ import annotations

import threading
import time


class TokenBucket:
    """
    Simple in-process token bucket rate limiter.
    Limits outgoing requests even if Streamlit reruns or multiple users hit the app.
    """

    def __init__(self, rate_per_sec: float, burst: int):
        if rate_per_sec <= 0:
            raise ValueError("rate_per_sec must be > 0")
        if burst <= 0:
            raise ValueError("burst must be > 0")
        self.rate = float(rate_per_sec)
        self.capacity = int(burst)
        self._tokens = float(burst)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens: float = 1.0, timeout_s: float | None = None) -> bool:
        deadline = None if timeout_s is None else (time.monotonic() + timeout_s)
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self._last
                if elapsed > 0:
                    self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
                    self._last = now
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

            if deadline is not None and time.monotonic() >= deadline:
                return False
            time.sleep(0.05)

