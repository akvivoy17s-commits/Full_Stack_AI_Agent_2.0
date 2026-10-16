import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

VERSION = "0.4.0"
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))
GENERATED_DIR = Path(os.getenv("GENERATED_DIR", ROOT / "generated_projects"))
TEMPLATES_DIR = ROOT / "templates"
DB_PATH = DATA_DIR / "app.db"
CHECKPOINT_DIR = DATA_DIR / "checkpoints"
EXPORT_DIR = DATA_DIR / "exports"
TMP_DIR = DATA_DIR / "tmp"
for _d in (DATA_DIR, GENERATED_DIR, CHECKPOINT_DIR, EXPORT_DIR, TMP_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Defaults for runtime-editable settings (overridden by values saved in SQLite via PUT /settings).
# Keep one model/base-URL pair per provider so switching the Settings dropdown does not
# overwrite another provider's configuration. API keys are never stored in SQLite.
from backend.agent.providers import PROVIDER_REGISTRY

_default_provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
if _default_provider not in PROVIDER_REGISTRY:
    _default_provider = "ollama"

_fallback_provider = os.getenv("LLM_FALLBACK_PROVIDER", "").strip().lower()
if _fallback_provider not in PROVIDER_REGISTRY or _fallback_provider == _default_provider:
    _fallback_provider = ""

DEFAULT_SETTINGS = {
    "provider": _default_provider,
    "fallback_provider": _fallback_provider,
    "max_retries": int(os.getenv("LLM_MAX_RETRIES", "2")),
    "vision_model": os.getenv("OLLAMA_VISION_MODEL", ""),
    "timeout_s": int(os.getenv("OLLAMA_TIMEOUT_S", "300")),
    "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "4096")),
    "generation_profile": os.getenv("GENERATION_PROFILE", "fast"),
    "ollama_keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "30m"),
    "max_concurrency": int(os.getenv("MAX_CONCURRENCY", "1")),
    "max_repair_loops": int(os.getenv("MAX_REPAIR_LOOPS", "3")),
}
for _provider_id, _meta in PROVIDER_REGISTRY.items():
    DEFAULT_SETTINGS[f"{_provider_id}_base_url"] = os.getenv(
        str(_meta["base_url_env"]), str(_meta["default_base_url"]))
    DEFAULT_SETTINGS[f"{_provider_id}_model"] = os.getenv(
        str(_meta["model_env"]), str(_meta["default_model"]))
# The previous release exposed these fields. Keep them available for older UI/code callers.
DEFAULT_SETTINGS["openai_base_url"] = os.getenv("OPENAI_BASE_URL", DEFAULT_SETTINGS["openai_base_url"])
DEFAULT_SETTINGS["openai_model"] = os.getenv("OPENAI_MODEL", DEFAULT_SETTINGS["openai_model"])

MAX_OUT_TOKENS = int(os.getenv("MAX_OUT_TOKENS", "4000"))
SECTION_MAX_TOKENS = int(os.getenv("SECTION_MAX_TOKENS", "2500"))
CONTEXT_BUDGET_CHARS = int(os.getenv("CONTEXT_BUDGET_CHARS", "3000"))
MAX_FILE_BYTES = 200_000
MAX_CHECKPOINTS = int(os.getenv("MAX_CHECKPOINTS", "20"))
MAX_ZIP_BYTES = 100_000_000
MOCK_LLM = os.getenv("MOCK_LLM", "0") == "1"          # offline test mode, no model needed
USE_BROWSER = os.getenv("USE_BROWSER", "1") == "1"    # Playwright checks + screenshots
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
ALLOWED_HOSTS = [h.strip().lower() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",") if h.strip()]   # Host header allowlist ("*" disables)
API_TOKEN = os.getenv("API_TOKEN", "")                 # optional: when set, every request except /health must send it (X-API-Token, Bearer, or ?token=)
MAX_READ_BYTES = int(os.getenv("MAX_READ_BYTES", "1000000"))   # largest file the API will return
