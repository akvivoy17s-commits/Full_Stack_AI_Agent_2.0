import json
from backend.config import GENERATED_DIR
from backend.agent.state import AgentState


def _path(pid: str):
    d = GENERATED_DIR / pid / ".agent"
    d.mkdir(parents=True, exist_ok=True)
    return d / "state.json"


def save(state: AgentState) -> None:
    _path(state.project_id).write_text(json.dumps(state.to_dict(), indent=1), encoding="utf-8")


def load(pid: str) -> AgentState | None:
    p = _path(pid)
    return AgentState.from_dict(json.loads(p.read_text(encoding="utf-8"))) if p.exists() else None


def list_projects() -> list[str]:
    return sorted(d.name for d in GENERATED_DIR.iterdir() if (d / ".agent" / "state.json").exists())
