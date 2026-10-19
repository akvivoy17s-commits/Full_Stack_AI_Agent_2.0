"""Detect external-service configuration required by generated applications.

Only variable *names* and safe placeholders are stored in the spec. Secret values are
never accepted from prompts, written into generated files, or sent to the frontend.
"""
from __future__ import annotations

import re

# (integration id, provider match, environment variables)
# Each field is: name, purpose, placeholder, scope, secret.
_SERVICE_RULES = [
    ("openai", r"\b(openai|gpt[- ]?(3\.5|4|4o|4\.1|5)|chatgpt api)\b", [
        ("OPENAI_API_KEY", "OpenAI API key (server-side only)", "your-openai-api-key", "server", True),
    ]),
    ("gemini", r"\b(gemini api|google generative ai|gemini developer api)\b", [
        ("GEMINI_API_KEY", "Gemini API key (server-side only)", "your-gemini-api-key", "server", True),
    ]),
    ("anthropic", r"\b(anthropic api|claude api|anthropic claude)\b", [
        ("ANTHROPIC_API_KEY", "Anthropic API key (server-side only)", "your-anthropic-api-key", "server", True),
    ]),
    ("openrouter", r"\b(openrouter)\b", [
        ("OPENROUTER_API_KEY", "OpenRouter API key (server-side only)", "your-openrouter-api-key", "server", True),
    ]),
    ("deepseek", r"\b(deepseek api|deepseek)\b", [
        ("DEEPSEEK_API_KEY", "DeepSeek API key (server-side only)", "your-deepseek-api-key", "server", True),
    ]),
    ("google-maps", r"\b(google maps api|google maps|places api|geocoding api)\b", [
        ("GOOGLE_MAPS_API_KEY", "Google Maps/Places API key (keep server-side unless using a domain-restricted browser key)", "your-google-maps-api-key", "server", True),
    ]),
    ("openweather", r"\b(openweathermap|openweather api)\b", [
        ("OPENWEATHER_API_KEY", "OpenWeather API key", "your-openweather-api-key", "server", True),
    ]),
    ("weatherapi", r"\b(weatherapi(?:\.com)? api|weatherapi\.com|weatherapi)\b", [
        ("WEATHERAPI_API_KEY", "WeatherAPI.com API key", "your-weatherapi-api-key", "server", True),
    ]),
    ("tmdb", r"\b(tmdb|the movie database api)\b", [
        ("TMDB_API_KEY", "The Movie Database API key", "your-tmdb-api-key", "server", True),
    ]),
    ("youtube-data", r"\b(youtube data api|youtube api v3)\b", [
        ("YOUTUBE_API_KEY", "YouTube Data API key", "your-youtube-api-key", "server", True),
    ]),
    ("spotify", r"\b(spotify api|spotify developer api)\b", [
        ("SPOTIFY_CLIENT_ID", "Spotify application client id", "your-spotify-client-id", "server", False),
        ("SPOTIFY_CLIENT_SECRET", "Spotify application client secret", "your-spotify-client-secret", "server", True),
    ]),
    ("github", r"\b(github api|github personal access token|github oauth)\b", [
        ("GITHUB_TOKEN", "GitHub API token (server-side only)", "your-github-token", "server", True),
    ]),
    ("supabase", r"\b(supabase)\b", [
        ("SUPABASE_URL", "Supabase project URL", "https://your-project.supabase.co", "server", False),
        ("SUPABASE_ANON_KEY", "Supabase anon/publishable key (do not rely on it as authorization; enable RLS)", "your-supabase-anon-key", "public", False),
        ("SUPABASE_SERVICE_ROLE_KEY", "Supabase service-role key (server-side only; bypasses RLS)", "your-supabase-service-role-key", "server", True),
    ]),
    ("resend", r"\b(resend email|resend\.com|resend api)\b", [
        ("RESEND_API_KEY", "Resend email API key (server-side only)", "your-resend-api-key", "server", True),
    ]),
    ("sendgrid", r"\b(sendgrid|twilio sendgrid)\b", [
        ("SENDGRID_API_KEY", "SendGrid API key (server-side only)", "your-sendgrid-api-key", "server", True),
    ]),
    ("twilio", r"\b(twilio sms|twilio api|twilio)\b", [
        ("TWILIO_ACCOUNT_SID", "Twilio account SID", "your-twilio-account-sid", "server", False),
        ("TWILIO_AUTH_TOKEN", "Twilio authentication token (server-side only)", "your-twilio-auth-token", "server", True),
        ("TWILIO_PHONE_NUMBER", "Twilio sender phone number", "+10000000000", "server", False),
    ]),
    ("cloudinary", r"\b(cloudinary)\b", [
        ("CLOUDINARY_CLOUD_NAME", "Cloudinary cloud name", "your-cloud-name", "server", False),
        ("CLOUDINARY_API_KEY", "Cloudinary API key", "your-cloudinary-api-key", "server", False),
        ("CLOUDINARY_API_SECRET", "Cloudinary API secret (server-side only)", "your-cloudinary-api-secret", "server", True),
    ]),
    ("clerk", r"\b(clerk authentication|clerk auth|clerk\.com)\b", [
        ("CLERK_PUBLISHABLE_KEY", "Clerk publishable key (frontend-safe by design)", "your-clerk-publishable-key", "public", False),
        ("CLERK_SECRET_KEY", "Clerk secret key (server-side only)", "your-clerk-secret-key", "server", True),
    ]),
    ("auth0", r"\b(auth0)\b", [
        ("AUTH0_DOMAIN", "Auth0 tenant domain", "your-tenant.us.auth0.com", "server", False),
        ("AUTH0_CLIENT_ID", "Auth0 application client id", "your-auth0-client-id", "server", False),
        ("AUTH0_CLIENT_SECRET", "Auth0 application client secret", "your-auth0-client-secret", "server", True),
    ]),
    ("google-oauth", r"\b(google oauth|sign in with google|google login)\b", [
        ("GOOGLE_CLIENT_ID", "Google OAuth client id", "your-google-client-id", "server", False),
        ("GOOGLE_CLIENT_SECRET", "Google OAuth client secret (server-side only)", "your-google-client-secret", "server", True),
    ]),
    ("aws", r"\b(aws (?:sdk|api|translate|textract|comprehend)|amazon (?:translate|textract|comprehend) api)\b", [
        ("AWS_REGION", "AWS region for the requested service", "ap-south-1", "server", False),
        ("AWS_ACCESS_KEY_ID", "AWS access key id (prefer workload identity in production)", "your-aws-access-key-id", "server", True),
        ("AWS_SECRET_ACCESS_KEY", "AWS secret access key (prefer workload identity in production)", "your-aws-secret-access-key", "server", True),
    ]),
]

_GENERIC_EXTERNAL_RE = re.compile(
    r"\b(external api|third[- ]party api|third party service|external service|"
    r"api key|api token|api credentials|"
    r"integrat(?:e|es|ed|ing) with .{1,60} api|connect(?:s|ed|ing)? to .{1,60} api)\b",
    re.I,
)
_GENERIC_NAMED_API_RE = re.compile(
    r"\b(?:integrat(?:e|es|ed|ing)\s+with|connect(?:s|ed|ing)?\s+to|"
    r"us(?:e|es|ed|ing)|call(?:s|ed|ing)?|consum(?:e|es|ed|ing)|"
    r"fetch(?:es|ed|ing)?(?:\s+data)?\s+from|retriev(?:e|es|ed|ing)(?:\s+data)?\s+from|"
    r"get(?:s|ting)?\s+data\s+from|quer(?:y|ies|ied|ying))\s+(?:the\s+)?"
    r"([A-Za-z][A-Za-z0-9 ._-]{1,35}?)\s+(?:REST\s+)?API\b", re.I
)
_GENERIC_NAMED_KEY_RE = re.compile(
    r"\b((?!(?:the|a|an|your|our|external|third[- ]party)\b)[A-Z][A-Za-z0-9_-]{1,35})\s+API\s+(?:key|token|credentials?)\b|"
    r"\bAPI\s+(?:key|token|credentials?)\s+(?:for|from)\s+([A-Za-z][A-Za-z0-9_-]{1,35})\b", re.I
)
_GENERIC_STOP = {"external", "third party", "third-party", "a", "an", "our", "your", "backend", "frontend", "rest", "the"}


def _entry(name: str, purpose: str, placeholder: str, scope: str, secret: bool, integration: str) -> dict:
    return {"name": name, "scope": scope, "secret": bool(secret), "placeholder": placeholder,
            "purpose": purpose, "integration": integration}


def detect(text: str) -> list[dict]:
    """Return environment contract entries for named external services in a brief.

    Provider-specific names are preferred. An unrecognised explicitly external API gets
    generic server-only keys rather than a fabricated vendor-specific contract.
    """
    text = str(text or "")
    found: list[dict] = []
    found_names: set[str] = set()
    found_integrations: set[str] = set()
    for integration, pattern, variables in _SERVICE_RULES:
        if not re.search(pattern, text, re.I):
            continue
        found_integrations.add(integration)
        for name, purpose, placeholder, scope, secret in variables:
            if name not in found_names:
                found.append(_entry(name, purpose, placeholder, scope, secret, integration))
                found_names.add(name)

    named_api = _GENERIC_NAMED_API_RE.search(text)
    named_key = _GENERIC_NAMED_KEY_RE.search(text)
    # Named API mentions and named API-key mentions are sufficient by themselves:
    # briefs do not always use the phrase "external API".
    if not found_integrations and (_GENERIC_EXTERNAL_RE.search(text) or named_api or named_key):
        m = named_api
        if named_key and not m:
            label = named_key.group(1) or named_key.group(2) or ""
        else:
            label = m.group(1) if m else ""
        label = re.sub(r"[^a-zA-Z0-9]+", " ", label).strip()
        if label and label.lower() not in _GENERIC_STOP:
            stem = re.sub(r"[^A-Z0-9]+", "_", label.upper()).strip("_")[:28] or "EXTERNAL"
            integration = stem.lower().replace("_", "-")
            name = f"{stem}_API_KEY"
            found.append(_entry(name, f"{label} API key (server-side only)", f"your-{integration}-api-key", "server", True, integration))
            found_names.add(name)
        else:
            integration = "external-api"
            found.append(_entry("EXTERNAL_API_BASE_URL", "Base URL of the external API", "https://api.example.com", "server", False, integration))
            found.append(_entry("EXTERNAL_API_KEY", "External API key (server-side only)", "your-external-api-key", "server", True, integration))
    return found


def external_entries(spec: dict) -> list[dict]:
    """Only server-side values that belong to a named integration, excluding public keys."""
    out = []
    for entry in spec.get("env", []):
        if entry.get("scope") == "server" and entry.get("integration") and entry.get("name"):
            out.append(entry)
    return out


def public_entries(spec: dict) -> list[dict]:
    """Frontend-safe environment entries. Secret-marked values can never cross this boundary."""
    return [e for e in spec.get("env", []) if e.get("scope") == "public" and not e.get("secret")]
