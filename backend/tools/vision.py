"""Optional screenshot analysis. Runs ONLY when a vision-capable Ollama model is configured AND installed
(Settings -> vision model, e.g. llava:7b / qwen2.5vl:7b). A text-only coding model is never sent images.
Findings are advisory warnings (they never block 'done' and are never auto-repaired)."""
import base64

from backend import config
from backend.agent import llm, prompts, schemas
from backend.storage import db


def analyze(images: dict[str, bytes], sections: list[str]) -> dict:
    s = db.get_settings()
    vm = (s.get("vision_model") or "").strip()
    if not vm:
        return {"status": "skipped", "note": "no vision model configured (optional): deterministic checks only", "findings": []}
    if not images:
        return {"status": "skipped", "note": "no screenshots were captured", "findings": []}
    if not config.MOCK_LLM:
        st = llm.status()
        if not st["reachable"]:
            return {"status": "skipped", "note": f"{st.get('provider', 'Ollama')} is unreachable: visual analysis skipped", "findings": []}
        if not st["vision_available"]:
            return {"status": "skipped", "note": f"vision model '{vm}' is not available (Ollama: ollama pull {vm}): visual analysis skipped", "findings": []}
    findings, errors = [], 0
    for name, raw in images.items():
        try:
            data, _ = llm.call_json("vision", prompts.VISION, f"VIEWPORT: {name}. SECTIONS: {','.join(sections)}", vm, 400,
                                    schema=schemas.VisionOut, images=[base64.b64encode(raw).decode()])
        except llm.OllamaError as e:
            errors += 1
            if e.code in ("offline", "model_missing"):
                break
            continue
        for it in data.get("issues", [])[:4]:
            if isinstance(it, dict) and str(it.get("msg", "")).strip():
                sid = str(it.get("sid", ""))
                findings.append({"viewport": name, "sid": sid if sid in sections else "", "msg": str(it["msg"])[:160]})
    status = "ok" if errors == 0 else ("partial" if findings else "failed")
    return {"status": status, "note": f"{vm}: {len(findings)} finding(s)" + (f", {errors} call(s) failed" if errors else ""), "findings": findings[:8]}
