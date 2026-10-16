from dataclasses import dataclass, field, asdict

PHASES = ("init", "plan", "design", "code", "verify", "done")


@dataclass
class AgentState:
    project_id: str
    brief: str
    phase: str = "init"
    plan: dict = field(default_factory=dict)     # sections, pages, stack
    design: dict = field(default_factory=dict)   # tokens: colors, fonts, spacing, motion
    files: dict = field(default_factory=dict)    # path -> short hash
    errors: list = field(default_factory=list)
    repair_count: int = 0
    motion: dict = field(default_factory=dict)
    sections_done: list = field(default_factory=list)
    usage: dict = field(default_factory=lambda: {"in": 0, "out": 0})
    stack: str = "html"                          # html | react (React + Vite + TypeScript)
    layout: str = "landing"                      # landing | dashboard | portfolio
    spec_digest: str = ""                               # one-line app spec summary (from backend.spec), used only in the blueprint call
    stack_config: dict = field(default_factory=dict)   # {mode, stack{frontend,backend,database,...}, sources, reasons} from backend.stack

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "AgentState":
        return cls(**d)

    def compact(self, max_chars: int = 1500) -> str:
        """Tiny context string sent to the LLM instead of full history/files."""
        parts = [f"BRIEF: {self.brief[:400]}", f"PHASE: {self.phase}"]
        if self.plan:
            parts.append("PLAN: " + ",".join(s if isinstance(s, str) else s.get("id", "?")
                                              for s in self.plan.get("sections", [])))
        if self.design:
            parts.append("DESIGN: " + ";".join(f"{k}={v}" for k, v in list(self.design.items())[:10]))
        if self.files:
            parts.append("FILES: " + ",".join(self.files))
        if self.errors:
            parts.append("ERRORS: " + " | ".join(e[:150] for e in self.errors[-3:]))
        return "\n".join(parts)[:max_chars]
