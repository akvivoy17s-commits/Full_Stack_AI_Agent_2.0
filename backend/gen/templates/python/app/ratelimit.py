import threading
import time

from .config import cfg
from .errors import ApiError


class Limiter:
    """Fixed-window limiter kept in memory (per process). Behind several workers/instances use a shared store such as Redis."""

    def __init__(self, limit: int, window_s: int = 900):
        self.limit, self.window, self.hits, self.lock = limit, window_s, {}, threading.Lock()

    def enforce(self, key: str) -> None:
        if cfg.env == "test":
            return
        now = time.monotonic()
        with self.lock:
            if len(self.hits) > 10000:
                self.hits = {k: v for k, v in self.hits.items() if v[0] > now}
            start, n = self.hits.get(key, (now + self.window, 0))
            if start <= now:
                start, n = now + self.window, 0
            self.hits[key] = (start, n + 1)
            over = n + 1 > self.limit
        if over:
            raise ApiError(429, "rate_limited", "Too many requests, try again later")


def pick_ip(remote: str | None, forwarded: str | None) -> str:
    """Client address for rate limiting. X-Forwarded-For is trusted only when TRUST_PROXY=<number of proxies in front of the app>."""
    n = int(cfg.trust_proxy) if cfg.trust_proxy.isdigit() else 0
    if n and forwarded:
        hops = [h.strip() for h in forwarded.split(",") if h.strip()]
        if len(hops) >= n:
            return hops[-n]
    return remote or "unknown"
