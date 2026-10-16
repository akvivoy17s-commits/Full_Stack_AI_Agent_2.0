"""Read cache: Redis when REDIS_URL is set and reachable, otherwise a small in-memory TTL map. A cache failure never fails a request."""
import json
import logging
import threading
import time

from .config import cfg

log = logging.getLogger("app")
_mem: dict[str, tuple[float, str]] = {}
_lock = threading.Lock()
_ver = 1
_redis = None
_tried = False


def _client():
    global _redis, _tried
    if not cfg.redis_url:
        return None
    if not _tried:
        _tried = True
        try:
            import redis
            c = redis.Redis.from_url(cfg.redis_url, socket_connect_timeout=2, socket_timeout=2)
            c.ping()
            _redis = c
        except Exception:  # noqa: BLE001  any failure means "use memory"
            log.warning("Redis unavailable, using the in-memory cache")
    return _redis


def backend() -> str:
    return "redis" if _client() else "memory"


def version() -> str:
    try:
        c = _client()
        if c:
            return (c.get("cache:ver") or b"0").decode()
    except Exception:  # noqa: BLE001
        pass
    return str(_ver)


def get(key: str):
    try:
        c = _client()
        if c:
            v = c.get(key)
            return json.loads(v) if v else None
    except Exception:  # noqa: BLE001
        return None
    with _lock:
        hit = _mem.get(key)
        if not hit or hit[0] < time.time():
            _mem.pop(key, None)
            return None
        return json.loads(hit[1])


def set(key: str, value) -> None:  # noqa: A001
    text = json.dumps(value)
    try:
        c = _client()
        if c:
            c.set(key, text, ex=cfg.cache_ttl)
            return
    except Exception:  # noqa: BLE001
        return
    with _lock:
        if len(_mem) >= 500:
            _mem.pop(next(iter(_mem)))
        _mem[key] = (time.time() + cfg.cache_ttl, text)


def invalidate() -> None:
    """Any successful write bumps the version, so every cached read becomes unreachable at once (entries then expire by TTL)."""
    global _ver
    with _lock:
        _ver += 1
    try:
        c = _client()
        if c:
            c.incr("cache:ver")
    except Exception:  # noqa: BLE001
        pass
