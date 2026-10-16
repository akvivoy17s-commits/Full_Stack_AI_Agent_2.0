"""Phase 6: bounded self-repair for project FILES (JS / Python / JSON syntax errors; extra checks can be plugged in).

Token-cheap: one small LLM call per broken file, only a ~30 line window is sent, answer = unique-match patches.
Bounded: max rounds, max tries per issue, token budget, stops when nothing changes, rolls back a round that made things worse.
Safe: tests, secrets, lockfiles and .agent/ are never edited; patches that add check-suppression markers are rejected.
"""
import hashlib
import json
import re

from backend.agent import context
from backend.storage import db
from backend.tools import terminal

MAX_ROUNDS, MAX_TRIES, TOKEN_BUDGET = 3, 2, 12000
MAX_FILES_PER_ROUND, MAX_MSGS_PER_FILE = 3, 4
EDITABLE = (".js", ".mjs", ".cjs", ".py", ".json", ".ts", ".tsx", ".jsx", ".css")

PROTECTED = re.compile(
    r"(^|/)(tests?|__tests__|\.agent|node_modules|\.git)/|(^|/)(conftest\.py|package-lock\.json|\.env[^/]*)$|"
    r"(\.test\.|\.spec\.|_test\.py$|(^|/)test_[^/]*\.py$)", re.I)
SUPPRESS = re.compile(r"eslint-disable|@ts-ignore|@ts-nocheck|noqa|type:\s*ignore|pragma:\s*no cover|\.skip\(|pytest\.mark\.skip|--no-verify", re.I)

SYSTEM = ('You fix one broken source file. Return ONLY JSON {"patches":[{"old":"exact text copied from the given code, '
          'unique in the file, <=300 chars","new":"replacement"}]}. At most 3 patches. Smallest change that fixes the listed errors. '
          'Never add lint/type/test suppression comments, never remove tests or security checks, never touch anything else.')


def _sig(file: str, msg: str) -> str:
    return hashlib.md5(f"{file}|{msg}".encode()).hexdigest()[:10]


def _issue(file: str, msg: str, line: int | None = None) -> dict:
    return {"sid": None, "file": file, "line": line, "msg": f"{file}: {msg}"[:240]}


# ------------------------------------------------------------------ checks (in-process or allowlisted node; no shell)
def static_issues(pf) -> list[dict]:
    out = []
    for path in pf.tree():
        if path.startswith("node_modules") or not path.endswith(EDITABLE):
            continue
        try:
            text = pf.read(path)
        except (OSError, ValueError):
            continue
        if path.endswith(".py"):
            try:
                compile(text, path, "exec")
            except SyntaxError as e:
                out.append(_issue(path, f"SyntaxError: {e.msg} (line {e.lineno})", e.lineno))
        elif path.endswith(".json"):
            try:
                json.loads(text)
            except ValueError as e:
                out.append(_issue(path, f"invalid JSON: {str(e)[:100]}", getattr(e, "lineno", None)))
        elif path.endswith((".js", ".mjs", ".cjs")):
            r = terminal.run(["node", "--check", path], cwd=str(pf.root))
            if r["code"] not in (0, 127):
                m = re.search(rf"{re.escape(path)}:(\d+)", r["out"])
                out.append(_issue(path, r["out"].strip()[:200], int(m.group(1)) if m else None))
        # TypeScript/TSX/JSX/CSS syntax is validated by the project's real npm build, not node --check.
    return out


# ------------------------------------------------------------------ patching
def _window(text: str, line: int | None, budget: int = 1800) -> str:
    """~30 lines around the error, but always containing the error line even when generated lines are very long."""
    if not line:
        return text[:budget]
    lines = text.splitlines()
    if not lines:
        return ""
    idx = min(max(line - 1, 0), len(lines) - 1)
    target = lines[idx][: budget * 2 // 3]
    lo = hi = idx
    size = len(target)
    while size < budget and (lo > max(0, idx - 15) or hi < min(len(lines) - 1, idx + 14)):
        if lo > max(0, idx - 15) and size + len(lines[lo - 1]) + 1 <= budget:
            lo -= 1
            size += len(lines[lo]) + 1
        elif hi < min(len(lines) - 1, idx + 14) and size + len(lines[hi + 1]) + 1 <= budget:
            hi += 1
            size += len(lines[hi]) + 1
        else:
            break
    return "\n".join(lines[lo:idx] + [target] + lines[idx + 1: hi + 1])


def _valid_patch(p) -> bool:
    if not isinstance(p, dict) or not isinstance(p.get("old"), str) or not isinstance(p.get("new"), str):
        return False
    return 0 < len(p["old"]) <= 300 and len(p["new"]) <= 1500 and p["old"] != p["new"] and not SUPPRESS.search(p["new"])


def _apply(text: str, patches: list) -> str | None:
    """All-or-nothing: every patch must be valid and match exactly once."""
    if not patches or len(patches) > 3 or not all(_valid_patch(p) for p in patches):
        return None
    for p in patches:
        if text.count(p["old"]) != 1:
            return None
        text = text.replace(p["old"], p["new"])
    return text


def _default_call(user: str):
    from backend.agent import llm          # lazy: keeps this module importable/testable without the model stack
    return llm.call_json("repair", SYSTEM, user, None, 900)


# ------------------------------------------------------------------ the loop
def repair_files(pf, issues: list[dict] | None = None, check=None, call=None, max_rounds: int = MAX_ROUNDS,
                 max_tries: int = MAX_TRIES, token_budget: int = TOKEN_BUDGET) -> dict:
    """Returns {status: PASS|PARTIAL|FAIL|BLOCKED, remaining, blocked, fixed, rounds, attempts, usage, stop, log}."""
    check, call = check or static_issues, call or _default_call
    issues = list(check(pf) if issues is None else issues)
    pid, tid = pf.root.name, (context.current().task_id if context.current() else "")
    tries: dict[str, int] = {}
    log, fixed, used, stop, attempts, seen = [], 0, 0, "", 0, set()

    def rec(i, rnd, outcome):
        log.append({"round": rnd, "file": i["file"], "issue": i["msg"][:120], "outcome": outcome})
        db.add_repair_attempt(pid, tid, rnd, i["file"], i["msg"], _sig(i["file"], i["msg"]), "file_patch", outcome)

    def split(items):
        fix, blk, spent = [], [], []
        for i in items:
            f = i.get("file")
            if not f or PROTECTED.search(f) or not f.endswith(EDITABLE):
                blk.append(i)
            elif tries.get(_sig(f, i["msg"]), 0) >= max_tries:
                spent.append(i)
            else:
                fix.append(i)
        return fix, blk, spent

    rounds = 0
    for rnd in range(1, max_rounds + 1):
        context.check()
        fix, blk, spent = split(issues)
        key = frozenset(_sig(i.get("file") or "", i["msg"]) for i in issues)
        if not fix:
            stop = "nothing repairable left" if issues else ""
            break
        if key in seen:
            stop = "no progress (same failures as an earlier round)"
            break
        if used >= token_budget:
            stop = f"token budget reached ({token_budget})"
            break
        seen.add(key)
        rounds = rnd
        by: dict[str, list[dict]] = {}
        for i in fix:
            by.setdefault(i["file"], []).append(i)
        backups, touched = {}, []
        for f, group in list(by.items())[:MAX_FILES_PER_ROUND]:
            for i in group:
                tries[_sig(f, i["msg"])] = tries.get(_sig(f, i["msg"]), 0) + 1
            attempts += 1
            try:
                text = pf.read(f)
                msgs = "\n".join(f"- {i['msg']}" for i in group[:MAX_MSGS_PER_FILE])
                data, u = call(f"FILE: {f}\nERRORS:\n{msgs}\nCODE (window):\n{_window(text, group[0].get('line'))}")
                used += u["in"] + u["out"]
                new = _apply(text, data.get("patches") or [])
            except Exception as e:  # noqa: BLE001  (a failed repair attempt must never crash the task)
                for i in group:
                    rec(i, rnd, "error")
                context.progress("repair", f"{f}: repair call failed ({str(e)[:60]})", "warn")
                continue
            if new is None:
                for i in group:
                    rec(i, rnd, "patch_rejected")
                continue
            backups[f] = text
            pf.write(f, new)
            touched.append((f, group))
            context.progress("repair", f"Patched {f} (round {rnd}/{max_rounds})")
        after = list(check(pf))
        if len(after) > len(issues):                                   # made things worse -> undo this round
            for f, text in backups.items():
                pf.write(f, text)
            for f, group in touched:
                for i in group:
                    rec(i, rnd, "rolled_back")
            context.progress("repair", "Repair made things worse; changes rolled back", "warn")
            after = list(issues)                                       # files are restored -> same state as before the round; skip a full re-check
        else:
            now = {_sig(i.get("file") or "", i["msg"]) for i in after}
            for f, group in touched:
                for i in group:
                    ok = _sig(f, i["msg"]) not in now
                    fixed += ok
                    rec(i, rnd, "fixed" if ok else "still_failing")
        issues = after
    else:
        stop = stop or ("max rounds reached" if issues else "")
    if not issues:
        status = "PASS"
    else:
        fix, blk, spent = split(issues)
        status = "PARTIAL" if fixed else ("BLOCKED" if blk and not fix and not spent and not attempts else "FAIL")
        if spent and not stop:
            stop = f"issue(s) tried {max_tries}x without success"
    fix, blk, spent = split(issues)
    return {"status": status, "remaining": issues, "blocked": [i["msg"] for i in blk], "fixed": fixed, "rounds": rounds,
            "attempts": attempts, "usage_tokens": used, "stop": stop, "log": log[-30:]}
