from backend.agent.orchestrator import _section_fixable


def test_markup_issue_uses_section_repair():
    issue = {"sid": "login", "msg": "section CSS invalid"}
    assert _section_fixable(issue, {}) is True


def test_typescript_build_issue_uses_file_repair_not_section_repair():
    issue = {
        "sid": "login",
        "file": "src/sections/Login.tsx",
        "line": 14,
        "msg": "build: src/sections/Login.tsx(14,10): error TS2322: type mismatch",
    }
    assert _section_fixable(issue, {}) is False


def test_non_section_issue_is_not_sent_to_section_repair():
    assert _section_fixable({"sid": None, "file": "vite.config.ts", "msg": "bad config"}, {}) is False


def test_section_issue_is_not_retried_after_limit():
    issue = {"sid": "login", "msg": "section empty"}
    # same signature as orchestrator._sig() to cover retry gating
    from backend.agent.orchestrator import _sig, MAX_TRIES_PER_ISSUE
    assert _section_fixable(issue, {_sig(issue): MAX_TRIES_PER_ISSUE}) is False
