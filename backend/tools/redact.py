"""Secret redaction for logs, task events and stored errors."""
import os
import re

_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-]{8,}"),
    re.compile(r"(?i)((?:api[_-]?key|token|secret|password|authorization)[\"']?\s*[:=]\s*[\"']?)[^\s\"',;]{4,}"),
]
_SENSITIVE_ENV = re.compile(r"(?i)(key|token|secret|password|passwd)")


def redact(text) -> str:
    t = str(text)
    for k, v in os.environ.items():              # literal env secrets
        if len(v) >= 8 and _SENSITIVE_ENV.search(k):
            t = t.replace(v, "[REDACTED]")
    for p in _PATTERNS[:3]:
        t = p.sub("[REDACTED]", t)
    return _PATTERNS[3].sub(lambda m: m.group(1) + "[REDACTED]", t)
