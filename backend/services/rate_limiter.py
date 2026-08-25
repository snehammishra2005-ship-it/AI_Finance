"""
Simple in-process rate limiting (abuse control).

A token-bucket limiter keyed by an arbitrary identity string (a user id for
authenticated endpoints, a client IP for the pre-auth login/register endpoints).
Token buckets give smooth per-identity limits with a small burst allowance.

Scope / limitation: state is in-memory, so limits are enforced PER PROCESS. That
is correct for a single backend instance; when the app scales horizontally
(production-readiness P1 #7) this should be backed by a shared store such as
Redis so the limit is global. Idle buckets are evicted (LRU cap) so memory stays
bounded no matter how many distinct identities appear.

Pure and deterministic (the clock is injectable), so it unit-tests offline with
no FastAPI, no network, and no real time.
"""

import os
import time
import threading
from collections import OrderedDict


class RateLimiter:
    def __init__(self, capacity, refill_per_sec, max_keys=10000, time_func=time.monotonic):
        # capacity      : max tokens (the burst size)
        # refill_per_sec: tokens added per second (the sustained rate)
        self.capacity = float(capacity)
        self.refill_per_sec = float(refill_per_sec)
        self.max_keys = max_keys
        self._now = time_func
        self._buckets = OrderedDict()  # key -> [tokens, last_ts]
        self._lock = threading.Lock()

    def check(self, key):
        """
        Attempt to consume one token for `key`.
        Returns (allowed: bool, retry_after_seconds: float). Consumes a token
        only when allowed.
        """
        now = self._now()
        with self._lock:
            tokens, last = self._buckets.get(key, (self.capacity, now))
            # Refill based on elapsed time, capped at capacity.
            tokens = min(self.capacity, tokens + (now - last) * self.refill_per_sec)

            if tokens >= 1.0:
                tokens -= 1.0
                allowed, retry = True, 0.0
            else:
                allowed = False
                # Seconds until one token is available again.
                retry = (1.0 - tokens) / self.refill_per_sec if self.refill_per_sec > 0 else 3600.0

            self._buckets[key] = (tokens, now)
            self._buckets.move_to_end(key)

            # Bound memory: drop the least-recently-used buckets.
            while len(self._buckets) > self.max_keys:
                self._buckets.popitem(last=False)

            return allowed, retry


def _int(env_var, default):
    try:
        return int(os.getenv(env_var, default))
    except (TypeError, ValueError):
        return default


def _per_minute(rpm, burst=None):
    """Build a limiter from a requests-per-minute rate (burst defaults to rpm)."""
    return RateLimiter(capacity=burst or rpm, refill_per_sec=rpm / 60.0)


# Per authenticated user, across the normal API (chat, RAG, analysis, metrics).
# Generous enough for interactive use (incl. client retries), tight enough to
# stop a script from hammering the paid LLM/Tavily budget.
API_LIMITER = _per_minute(_int("RATE_LIMIT_API_RPM", 120))

# Per client IP, on the unauthenticated login/register endpoints — a brute-force
# / account-spam guard.
AUTH_LIMITER = _per_minute(_int("RATE_LIMIT_AUTH_RPM", 10))

# Per authenticated user, on file uploads specifically — uploads are heavier
# (extraction + RAG indexing + disk), so throttle them harder than plain chat.
# Default: ~30 uploads per 5 minutes, burst 30.
UPLOAD_LIMITER = RateLimiter(
    capacity=_int("RATE_LIMIT_UPLOAD_BURST", 30),
    refill_per_sec=_int("RATE_LIMIT_UPLOAD_PER_5MIN", 30) / 300.0,
)
