"""Requirement analysis (rule based, 0 LLM tokens): turns the app spec into a checkable requirement list.

Each requirement has an honest status:
  covered  -> the selected stack can generate it now
  planned  -> supported later ("planned:N" in the catalog); NOT produced in this build
  gap      -> the brief implies it but the selected stack cannot deliver it
Open questions that make the build unreliable are returned as `blocking`.
"""
import re

from backend.stack import catalog as C

BLOCKING_QUESTIONS = {"backend-conflict"}          # contradictory brief: building anyway would guess


def _status(s: str) -> str:
    return "covered" if s in (C.READY, "done") else ("planned" if str(s).startswith("planned") else "gap")


def _req(rid: str, kind: str, text: str, status: str = "covered", source: str = "spec") -> dict:
    return {"id": rid, "kind": kind, "text": text[:200], "status": status, "source": source}


def analyze(spec: dict) -> dict:
    """spec (from backend.spec) -> {requirements, gaps, assumptions, questions, blocking, counts}."""
    plan = {s["id"]: _status(s["status"]) for s in spec.get("plan", [])}
    reqs = [_req(f"F{i + 1}", "functional", f, plan.get("pages", "covered")) for i, f in enumerate(spec.get("features", []))]
    reqs += [_req(f"P-{p['slug']}", "page", f"Page '{p['title']}'" + (" (login required)" if p.get("auth") else ""), plan.get("pages", "covered"))
             for p in spec.get("pages", [])]
    ents = spec.get("data", {}).get("entities", [])
    if ents:
        reqs.append(_req("D1", "data", f"Data model: {', '.join(e['name'] for e in ents[:8])}", plan.get("data", "covered")))
    routes = spec.get("api", {}).get("routes", [])
    if routes:
        reqs.append(_req("A1", "api", f"{len(routes)} API route(s) with input validation", plan.get("api", "covered")))
    if spec.get("auth", {}).get("enabled"):
        reqs.append(_req("S0", "security", f"Authentication ({spec['auth']['method']}) with server-side authorization", plan.get("auth", "covered")))
    reqs += [_req(f"S{i + 1}", "security", s, plan.get("api", "covered")) for i, s in enumerate(spec.get("security", [])[:6])]
    for i, it in enumerate(spec.get("integrations", [])):
        reqs.append(_req(f"I{i + 1}", "integration", f"Integration: {it}", plan.get("integrations", "covered")))
    t = spec.get("testing") or {}
    if t:
        reqs.append(_req("T1", "testing", "Automated tests: " + re.sub(r"\s+", " ", str(t))[:120], plan.get("tests", "covered")))
    gaps = list(spec.get("gaps", []))
    for g in gaps:
        reqs.append(_req(f"G{len(reqs)}", "gap", g, "gap"))
    qs = spec.get("open_questions", [])
    counts = {k: sum(1 for r in reqs if r["status"] == k) for k in ("covered", "planned", "gap")}
    return {"requirements": reqs, "gaps": gaps, "assumptions": list(spec.get("assumptions", [])), "questions": qs,
            "blocking": [q for q in qs if q.get("id") in BLOCKING_QUESTIONS], "counts": counts}
