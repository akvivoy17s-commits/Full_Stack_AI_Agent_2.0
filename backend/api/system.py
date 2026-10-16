from fastapi import APIRouter, HTTPException

from backend import config
from backend.agent import llm, providers
from backend.agent.schemas import OllamaCheck, SettingsUpdate
from backend.storage import db

router = APIRouter()


def _provider_catalog(settings: dict) -> list[dict]:
    """Public metadata for the UI. Never includes a key value."""
    catalog = []
    for provider_id, meta in providers.PROVIDER_REGISTRY.items():
        resolved = providers.provider_settings(settings, provider_id)
        key_name = meta.get("key_env_var")
        catalog.append({
            "id": provider_id,
            "name": meta["name"],
            "adapter": meta["adapter"],
            "base_url": resolved["base_url"],
            "model": resolved["model"],
            "default_model": meta["default_model"],
            "api_key_env_var": key_name,
            "api_key_required": bool(key_name),
            "api_key_set": providers.api_key_set(provider_id),
        })
    return catalog


def _safe_settings() -> dict:
    settings = db.get_settings()
    provider = settings.get("provider", "ollama")
    try:
        active = providers.provider_settings(settings, provider)
    except ValueError:
        provider = "ollama"
        active = providers.provider_settings(settings, provider)
    # Compatibility aliases help the existing UI; no credential value is exposed.
    return {
        **settings,
        "provider": provider,
        "base_url": active["base_url"],
        "model": active["model"],
        "adapter": active["adapter"],
        "api_key_set": providers.api_key_set(provider),
        "providers": _provider_catalog(settings),
    }


@router.get("/health")
def health():
    db.init()
    return {"ok": True, "version": config.VERSION, "db": True, "mock_llm": config.MOCK_LLM}


@router.get("/ollama/status")
def ollama_status():
    # Historic route retained; status now refers to whichever provider is active.
    return llm.status()


@router.post("/ollama/check")
def ollama_check(body: OllamaCheck):
    """Verify an endpoint/model before saving it in settings."""
    if body.provider and body.provider not in providers.PROVIDER_REGISTRY:
        raise HTTPException(422, "unsupported provider")
    return llm.status(body.base_url, body.model, body.provider)


@router.get("/ollama/models")
def ollama_models():
    """Compatibility route: return the selected provider's model list."""
    st = llm.status()
    if not st.get("reachable"):
        raise HTTPException(503, st.get("error") or "provider is not reachable")
    return {"models": st.get("models", []), "provider": st.get("provider")}


@router.get("/providers")
def list_providers():
    settings = db.get_settings()
    return {"active_provider": settings.get("provider", "ollama"), "providers": _provider_catalog(settings)}


@router.get("/providers/{provider}/models")
def provider_models(provider: str):
    if provider not in providers.PROVIDER_REGISTRY:
        raise HTTPException(404, "unsupported provider")
    st = llm.status(provider=provider)
    if not st.get("reachable"):
        raise HTTPException(503, st.get("error") or "provider is not reachable")
    return {"provider": provider, "models": st.get("models", []), "model": st.get("model"),
            "model_check": st.get("model_check", "unverified")}


@router.get("/settings")
def get_settings():
    return _safe_settings()


@router.put("/settings")
def put_settings(body: SettingsUpdate):
    # The API key and generic active model/base URL are deliberately not written as-is.
    payload = body.model_dump(exclude_none=True, exclude={"api_key", "clear_api_key", "model", "base_url"})
    current = db.get_settings()
    provider = str(payload.get("provider") or current.get("provider", "ollama"))
    if provider not in providers.PROVIDER_REGISTRY:
        raise HTTPException(422, "unsupported provider")
    fallback = payload.get("fallback_provider", current.get("fallback_provider", ""))
    if fallback and fallback not in providers.PROVIDER_REGISTRY:
        raise HTTPException(422, "unsupported fallback_provider")
    if fallback == provider:
        if "fallback_provider" in payload:
            raise HTTPException(422, "fallback_provider must be different from the active provider")
        payload["fallback_provider"] = ""
    payload["provider"] = provider

    if body.model is not None:
        payload[f"{provider}_model"] = body.model
    if body.base_url is not None:
        payload[f"{provider}_base_url"] = body.base_url

    try:
        if body.clear_api_key:
            providers.clear_api_key(provider)
        elif body.api_key is not None and body.api_key.strip():
            proposed_settings = {**current, **payload}
            destination = providers.provider_settings(proposed_settings, provider)["base_url"]
            # Validate the destination before persisting credentials, not only when a request is made.
            providers.check_destination(str(destination), body.api_key.strip(), provider)
            providers.set_api_key(provider, body.api_key)
    except providers.ProviderError as e:
        raise HTTPException(422, str(e)) from None
    except ValueError as e:
        raise HTTPException(422, str(e)) from None
    except RuntimeError as e:
        raise HTTPException(500, str(e)) from None

    db.save_settings(payload)
    audit_items = list(payload)
    if body.api_key is not None and body.api_key.strip():
        audit_items.append("api_key_updated")
    if body.clear_api_key:
        audit_items.append("api_key_cleared")
    db.audit("settings", detail=",".join(audit_items))
    # Deliberately do not echo the submitted API key.
    return _safe_settings()
