"""Firebase Storage through the Admin SDK: a PRIVATE bucket, files are only served through the API.
The service-account key comes from a file path in the environment and is never logged, returned or committed."""
from .config import cfg
from .errors import ApiError

_bucket = None


def _b():
    global _bucket
    if _bucket:
        return _bucket
    try:
        import firebase_admin
        from firebase_admin import credentials, storage
    except ImportError:
        raise ApiError(503, "firebase_unavailable", "Firebase is not available on this server")
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(cfg.firebase_service_account_path) if cfg.firebase_service_account_path else credentials.ApplicationDefault()
            opts = {"storageBucket": cfg.firebase_storage_bucket}
            if cfg.firebase_project_id:
                opts["projectId"] = cfg.firebase_project_id
            firebase_admin.initialize_app(cred, opts)
        _bucket = storage.bucket()
    except ApiError:
        raise
    except Exception:
        raise ApiError(503, "storage_unavailable", "File storage is not configured")
    return _bucket


def put(key: str, body: bytes, content_type: str) -> None:
    try:
        _b().blob(key).upload_from_string(body, content_type=content_type)
    except ApiError:
        raise
    except Exception:
        raise ApiError(502, "storage_error", "The file storage rejected the request")


def get(key: str) -> bytes | None:
    try:
        blob = _b().blob(key)
        return blob.download_as_bytes() if blob.exists() else None
    except ApiError:
        raise
    except Exception:
        raise ApiError(502, "storage_error", "The file storage rejected the request")
