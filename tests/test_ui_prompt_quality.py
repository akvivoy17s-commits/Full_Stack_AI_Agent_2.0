from backend.agent import prompts


def test_section_prompt_requires_art_directed_ui_quality():
    prompt = prompts.SECTION.lower()
    for phrase in (
        "premium ui quality",
        "clear focal point",
        "vary section composition",
        "360px mobile",
        "never imply a control works",
    ):
        assert phrase in prompt


def test_blueprint_prompt_selects_distinct_visual_direction():
    prompt = prompts.BLUEPRINT.lower()
    assert "specific visual direction" in prompt
    assert "signature visual motif" in prompt


def test_key_section_hints_are_more_specific_than_generic_cards():
    assert "memorable composition" in prompts.HINTS["hero"].lower()
    assert "believable" in prompts.HINTS["showcase"].lower()
    assert "distinct project preview" in prompts.HINTS["work"].lower()
