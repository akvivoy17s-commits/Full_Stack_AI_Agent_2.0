"""Pydantic schemas for model output and API payloads."""
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from backend.security import validate_base_url
from backend.agent.prompt_limits import EDIT_REPAIR_PROMPT_MAX_CHARS


class SectionOut(BaseModel):
    html: str = Field(min_length=10)
    css: str = ""


class BlueprintOut(BaseModel):
    # Keep this response schema aligned with prompts.BLUEPRINT. Fields not declared here
    # are discarded by Pydantic before planner.blueprint() can use them.
    brand: str = "Brand"
    stack: str = ""
    sections: list[str] = Field(default_factory=list)
    pages: list[dict[str, Any]] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    architecture: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""
    design: dict[str, Any] = Field(default_factory=dict)
    motion: dict[str, Any] = Field(default_factory=dict)
    motion: dict = Field(default_factory=dict)


class SettingsUpdate(BaseModel):
    # Generic fields used by the provider dropdown in the Settings dialog.
    provider: str | None = Field(default=None, min_length=1, max_length=40)
    fallback_provider: str | None = Field(default=None, max_length=40)
    base_url: str | None = None
    model: str | None = Field(default=None, min_length=1, max_length=150)
    # Transient secrets: endpoint consumes these, but they are excluded from DB updates/responses.
    api_key: str | None = Field(default=None, max_length=500, repr=False)
    clear_api_key: bool = False

    # Legacy per-provider fields are retained for compatibility with the previous UI.
    ollama_base_url: str | None = None
    ollama_model: str | None = Field(default=None, min_length=1, max_length=150)
    openai_base_url: str | None = None
    openai_model: str | None = Field(default=None, min_length=1, max_length=150)
    gemini_base_url: str | None = None
    gemini_model: str | None = Field(default=None, min_length=1, max_length=150)
    openrouter_base_url: str | None = None
    openrouter_model: str | None = Field(default=None, min_length=1, max_length=150)
    groq_base_url: str | None = None
    groq_model: str | None = Field(default=None, min_length=1, max_length=150)
    deepseek_base_url: str | None = None
    deepseek_model: str | None = Field(default=None, min_length=1, max_length=150)
    anthropic_base_url: str | None = None
    anthropic_model: str | None = Field(default=None, min_length=1, max_length=150)
    vision_model: str | None = Field(default=None, max_length=150)
    max_retries: int | None = Field(default=None, ge=0, le=4)
    timeout_s: int | None = Field(default=None, ge=10, le=3600)
    num_ctx: int | None = Field(default=None, ge=1024, le=32768)
    generation_profile: Literal["fast", "balanced", "quality"] | None = None
    max_concurrency: int | None = Field(default=None, ge=1, le=4)
    max_repair_loops: int | None = Field(default=None, ge=0, le=5)

    @field_validator("base_url", "ollama_base_url", "openai_base_url", "gemini_base_url",
                     "openrouter_base_url", "groq_base_url", "deepseek_base_url", "anthropic_base_url")
    @classmethod
    def _url(cls, v):
        return None if v is None else validate_base_url(v)

    @field_validator("model", "ollama_model", "openai_model", "gemini_model", "openrouter_model",
                     "groq_model", "deepseek_model", "anthropic_model", "vision_model")
    @classmethod
    def _model(cls, v):
        if v and not re.fullmatch(r"[A-Za-z0-9._:/@\-]+", v):
            raise ValueError("invalid model name")
        return v


class OllamaCheck(BaseModel):
    base_url: str | None = None
    model: str | None = Field(default=None, max_length=150)
    provider: str | None = Field(default=None, max_length=40)

    @field_validator("base_url")
    @classmethod
    def _url(cls, v):
        return None if v is None else validate_base_url(v)


class TaskCreate(BaseModel):
    kind: Literal["generate", "verify", "edit", "test"]
    force: bool = False                       # regenerate everything (destructive -> needs confirm)
    confirm: bool = False
    repair: bool = True
    deep: bool = False                         # optional backend build/test pass; never installs packages
    section: str = Field(default="", max_length=20)
    instruction: str = Field(default="", max_length=EDIT_REPAIR_PROMPT_MAX_CHARS)


class VisionOut(BaseModel):
    issues: list = Field(default_factory=list)
