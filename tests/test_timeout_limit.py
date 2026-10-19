"""Regression tests for the configurable agent timeout limit."""

import pytest
from pydantic import ValidationError

from backend.agent.schemas import SettingsUpdate


def test_timeout_accepts_new_3600_second_limit():
    assert SettingsUpdate(timeout_s=3600).timeout_s == 3600


def test_timeout_rejects_values_above_3600_seconds():
    with pytest.raises(ValidationError):
        SettingsUpdate(timeout_s=3601)


def test_timeout_still_rejects_values_below_minimum():
    with pytest.raises(ValidationError):
        SettingsUpdate(timeout_s=9)
