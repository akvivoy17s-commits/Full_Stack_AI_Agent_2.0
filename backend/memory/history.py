"""Rolling history with zero-LLM compaction: old entries fold into one short digest."""
import json
from backend.config import GENERATED_DIR, CONTEXT_BUDGET_CHARS

KEEP_RECENT = 6


def _file(pid: str):
    d = GENERATED_DIR / pid / ".agent"
    d.mkdir(parents=True, exist_ok=True)
    return d / "history.json"


def _load(pid: str) -> dict:
    f = _file(pid)
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"digest": "", "items": []}


def add(pid: str, role: str, text: str) -> None:
    h = _load(pid)
    h["items"].append({"r": role, "t": text[:400]})
    if len(h["items"]) > KEEP_RECENT * 2:                    # compact older items
        old, h["items"] = h["items"][:-KEEP_RECENT], h["items"][-KEEP_RECENT:]
        h["digest"] = (h["digest"] + " | " + "; ".join(f"{i['r']}:{i['t'][:60]}" for i in old))[-800:]
    _file(pid).write_text(json.dumps(h), encoding="utf-8")


def context(pid: str, budget: int = CONTEXT_BUDGET_CHARS) -> str:
    h = _load(pid)
    s = (f"DIGEST: {h['digest']}\n" if h["digest"] else "") + "\n".join(
        f"{i['r']}: {i['t']}" for i in h["items"])
    return s[-budget:]
