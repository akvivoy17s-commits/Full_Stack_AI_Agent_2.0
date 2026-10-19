"""Shared character limits for user-authored coding prompts.

The plain-text project brief is capped at 15k characters in the UI. The
composed brief sent by the advanced wizard includes a small design/motion
suffix, so API boundaries allow an additional 1k characters for that suffix.
"""

AUTOPILOT_PROMPT_MAX_CHARS = 15_000
USER_PROMPT_MAX_CHARS = 15_000
EDIT_REPAIR_PROMPT_MAX_CHARS = 15_000
COMPOSED_BRIEF_MAX_CHARS = USER_PROMPT_MAX_CHARS + 1_000
