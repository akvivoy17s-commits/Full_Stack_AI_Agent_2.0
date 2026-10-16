import os

from dotenv import load_dotenv

from . import schema

load_dotenv()


def _list(v: str) -> list[str]:
    return [s.strip() for s in (v or "").split(",") if s.strip()]


class Config:
    """Settings come from environment variables only (see .env.example). Nothing secret is hard-coded."""

    def __init__(self, env=None):
        e = env if env is not None else os.environ
        self.env = e.get("APP_ENV", "development")
        self.host = e.get("HOST", "127.0.0.1")
        self.port = int(e.get("PORT", "8000") or 8000)
        self.cors_origins = _list(e.get("CORS_ORIGINS", ""))
        self.trust_proxy = e.get("TRUST_PROXY", "0")
        self.database_url = e.get("DATABASE_URL") or e.get("MONGODB_URI") or ""
        self.database_ssl = e.get("DATABASE_SSL") == "true"
        self.auto_migrate = e.get("AUTO_MIGRATE") == "true"
        self.jwt_secret = e.get("JWT_SECRET", "")
        self.access_ttl_min = float(e.get("JWT_ACCESS_TTL_MIN", "15") or 15)
        self.refresh_ttl_days = float(e.get("JWT_REFRESH_TTL_DAYS", "7") or 7)
        self.redis_url = e.get("REDIS_URL", "")
        self.cache_ttl = int(e.get("CACHE_TTL_SECONDS", "30") or 30)
        self.upload_dir = e.get("UPLOAD_DIR", "./uploads")
        self.upload_max_bytes = int(e.get("UPLOAD_MAX_BYTES", str(5 * 1024 * 1024)) or 5 * 1024 * 1024)
        self.s3_endpoint = e.get("S3_ENDPOINT", "")
        self.s3_bucket = e.get("S3_BUCKET", "")
        self.s3_region = e.get("S3_REGION", "us-east-1") or "us-east-1"
        self.s3_access_key_id = e.get("S3_ACCESS_KEY_ID", "")
        self.s3_secret_access_key = e.get("S3_SECRET_ACCESS_KEY", "")
        self.firebase_project_id = e.get("FIREBASE_PROJECT_ID", "")
        self.firebase_service_account_path = e.get("FIREBASE_SERVICE_ACCOUNT_PATH", "")
        self.firebase_storage_bucket = e.get("FIREBASE_STORAGE_BUCKET", "")
        self.stripe_secret_key = e.get("STRIPE_SECRET_KEY", "")
        self.stripe_webhook_secret = e.get("STRIPE_WEBHOOK_SECRET", "")
        self.stripe_currency = (e.get("STRIPE_CURRENCY", "usd") or "usd").lower()
        self.razorpay_key_id = e.get("RAZORPAY_KEY_ID", "")
        self.razorpay_key_secret = e.get("RAZORPAY_KEY_SECRET", "")
        self.razorpay_webhook_secret = e.get("RAZORPAY_WEBHOOK_SECRET", "")
        self.razorpay_currency = (e.get("RAZORPAY_CURRENCY", "inr") or "inr").lower()
        self.paypal_client_id = e.get("PAYPAL_CLIENT_ID", "")
        self.paypal_client_secret = e.get("PAYPAL_CLIENT_SECRET", "")
        self.paypal_webhook_id = e.get("PAYPAL_WEBHOOK_ID", "")
        self.paypal_env = "live" if e.get("PAYPAL_ENV") == "live" else "sandbox"
        self.paypal_currency = (e.get("PAYPAL_CURRENCY", "usd") or "usd").lower()
        self.ws_max_clients = int(e.get("WS_MAX_CLIENTS", "500") or 500)
        self.bcrypt_rounds = 4 if self.env == "test" else 12

    @property
    def sql_url(self) -> str:
        """SQLAlchemy needs an explicit driver; accept the plain URLs people copy from hosting dashboards."""
        u = self.database_url
        for plain, full in (("postgresql://", "postgresql+psycopg://"), ("postgres://", "postgresql+psycopg://"), ("mysql://", "mysql+pymysql://"),
                            ("mssql://", "mssql+pymssql://"), ("sqlserver://", "mssql+pymssql://")):
            if u.startswith(plain):
                return full + u[len(plain):]
        return u

    def validate(self) -> None:
        errs = []
        if not 1 <= self.port <= 65535:
            errs.append("PORT must be a valid port number")
        if not self.cors_origins:
            errs.append("CORS_ORIGINS must list the allowed browser origins (comma separated)")
        if schema.SCHEMA["db"] and not self.database_url:
            errs.append("DATABASE_URL is required" + (" (MONGODB_URI is also accepted)" if schema.SCHEMA["db"] == "mongodb" else ""))
        if schema.SCHEMA["auth"]:
            if len(self.jwt_secret) < 32 or self.jwt_secret.startswith("<"):
                errs.append("JWT_SECRET must be a random string of at least 32 characters")
            if not (self.access_ttl_min > 0 and self.refresh_ttl_days > 0):
                errs.append("JWT_ACCESS_TTL_MIN and JWT_REFRESH_TTL_DAYS must be positive numbers")
        if errs:
            raise RuntimeError("Invalid configuration: " + "; ".join(errs))


cfg = Config()
