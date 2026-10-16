"""S3-compatible object storage (AWS S3, MinIO, Cloudflare R2, DigitalOcean Spaces) with Signature V4, standard library only (no SDK).
The bucket stays PRIVATE: files are only served through the API, which applies the same sign-in rule as local uploads."""
import hashlib
import hmac
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from .config import cfg
from .errors import ApiError


def _hmac(k: bytes, d: str) -> bytes:
    return hmac.new(k, d.encode(), hashlib.sha256).digest()


def _enc(s: str) -> str:
    return urllib.parse.quote(s, safe="-_.~")


def authorization(method, host, path, payload_hash, amz_date, region, key_id, secret) -> tuple[str, dict]:
    headers = {"host": host, "x-amz-content-sha256": payload_hash, "x-amz-date": amz_date}
    names = sorted(headers)
    signed = ";".join(names)
    canonical = "\n".join([method, "/".join(_enc(p) for p in path.split("/")), "", "".join(f"{n}:{headers[n]}\n" for n in names), signed, payload_hash])
    day = amz_date[:8]
    scope = f"{day}/{region}/s3/aws4_request"
    to_sign = "\n".join(["AWS4-HMAC-SHA256", amz_date, scope, hashlib.sha256(canonical.encode()).hexdigest()])
    k = _hmac(_hmac(_hmac(_hmac(("AWS4" + secret).encode(), day), region), "s3"), "aws4_request")
    sig = hmac.new(k, to_sign.encode(), hashlib.sha256).hexdigest()
    return f"AWS4-HMAC-SHA256 Credential={key_id}/{scope}, SignedHeaders={signed}, Signature={sig}", headers


def target(key: str) -> tuple[str, str, str]:
    """AWS endpoints use the virtual-hosted style (bucket.host); every other S3-compatible service uses path style (host/bucket)."""
    u = urllib.parse.urlparse(cfg.s3_endpoint)
    if u.hostname and (u.hostname == "amazonaws.com" or u.hostname.endswith(".amazonaws.com")):
        host = f"{cfg.s3_bucket}.{u.netloc}"
        return f"{u.scheme}://{host}/{key}", host, f"/{key}"
    return f"{u.scheme}://{u.netloc}/{cfg.s3_bucket}/{key}", u.netloc, f"/{cfg.s3_bucket}/{key}"


def configured() -> bool:
    vals = (cfg.s3_endpoint, cfg.s3_bucket, cfg.s3_access_key_id, cfg.s3_secret_access_key)
    return all(v and not v.startswith("your-") for v in vals)


def _send(method: str, key: str, body: bytes | None = None, content_type: str = ""):
    if not configured():
        raise ApiError(503, "storage_unavailable", "File storage is not configured")
    url, host, path = target(key)
    payload = body or b""
    amz_date = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    auth, headers = authorization(method, host, path, hashlib.sha256(payload).hexdigest(), amz_date, cfg.s3_region, cfg.s3_access_key_id, cfg.s3_secret_access_key)
    headers = {k: v for k, v in headers.items() if k != "host"}
    headers["Authorization"] = auth
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=body if method == "PUT" else None, method=method, headers=headers)
    try:
        return urllib.request.urlopen(req, timeout=15)
    except urllib.error.HTTPError as e:
        return e
    except Exception:
        raise ApiError(502, "storage_unreachable", "The file storage could not be reached")


def put(key: str, body: bytes, content_type: str) -> None:
    r = _send("PUT", key, body, content_type)
    if not 200 <= r.status < 300:
        raise ApiError(502, "storage_error", "The file storage rejected the request")


def get(key: str) -> bytes | None:
    r = _send("GET", key)
    if r.status == 404:
        return None
    if not 200 <= r.status < 300:
        raise ApiError(502, "storage_error", "The file storage rejected the request")
    return r.read()
