"""Request models for the stack API (pydantic only, so they are testable without FastAPI)."""
from typing import Literal

from pydantic import BaseModel, Field

from backend.agent.prompt_limits import COMPOSED_BRIEF_MAX_CHARS

Mode = Literal["automatic", "manual", "hybrid"]


class ResolveReq(BaseModel):
    mode: Mode = "automatic"
    prefs: dict[str, str | None] = Field(default_factory=dict)       # field -> id; "" / "auto" / null = let the engine decide
    brief: str = Field(default="", max_length=COMPOSED_BRIEF_MAX_CHARS)
    project_id: str | None = Field(default=None, max_length=64)       # when set, that project's stack counts as 'existing'
    options: bool = True                                              # include per-option allowed/why_not for the UI


class ApplyReq(BaseModel):
    mode: Mode = "hybrid"
    prefs: dict[str, str | None] = Field(default_factory=dict)
    confirm: bool = False                                             # required to change the frontend after code was generated
