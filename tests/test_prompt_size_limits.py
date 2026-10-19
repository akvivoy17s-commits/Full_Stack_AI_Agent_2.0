"""Regression tests for consistent UI/API prompt character limits."""
import pytest
from pydantic import ValidationError

from backend.agent.prompt_limits import (
    AUTOPILOT_PROMPT_MAX_CHARS,
    USER_PROMPT_MAX_CHARS,
    EDIT_REPAIR_PROMPT_MAX_CHARS,
    COMPOSED_BRIEF_MAX_CHARS,
)
from backend.agent.schemas import TaskCreate
from backend.api.autopilot import AutoBuildRequest
from backend.api.spec import PreviewReq
from backend.main import EditReq, NewProject
from backend.stack.schemas import ResolveReq


def test_autopilot_prompt_accepts_30000_and_rejects_30001():
    assert len(AutoBuildRequest(prompt="x" * AUTOPILOT_PROMPT_MAX_CHARS).prompt) == 30_000
    with pytest.raises(ValidationError):
        AutoBuildRequest(prompt="x" * (AUTOPILOT_PROMPT_MAX_CHARS + 1))


@pytest.mark.parametrize("model,kwargs", [
    (NewProject, {"framework": "react"}),
    (PreviewReq, {}),
    (ResolveReq, {}),
])
def test_composed_project_briefs_accept_16000_and_reject_16001(model, kwargs):
    brief = "x" * COMPOSED_BRIEF_MAX_CHARS
    assert len(model(brief=brief, **kwargs).brief) == COMPOSED_BRIEF_MAX_CHARS
    with pytest.raises(ValidationError):
        model(brief=brief + "x", **kwargs)


def test_edit_repair_instruction_accepts_15000_and_rejects_15001():
    instruction = "Fix the generated page. " + ("x" * (EDIT_REPAIR_PROMPT_MAX_CHARS - 24))
    assert len(TaskCreate(kind="edit", section="register", instruction=instruction).instruction) == EDIT_REPAIR_PROMPT_MAX_CHARS
    assert len(EditReq(section="register", instruction=instruction).instruction) == EDIT_REPAIR_PROMPT_MAX_CHARS
    with pytest.raises(ValidationError):
        TaskCreate(kind="edit", section="register", instruction=instruction + "x")
    with pytest.raises(ValidationError):
        EditReq(section="register", instruction=instruction + "x")


def test_user_prompt_limit_is_fifteen_thousand():
    assert USER_PROMPT_MAX_CHARS == 15_000
