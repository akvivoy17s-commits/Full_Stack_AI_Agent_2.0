"""Phase 6H.6: S3-compatible + Firebase Storage uploads for FastAPI, Flask, Django, NestJS and Spring (Express had both since 6A/6G).
Pure Python checks; the signing cross-check runs when node is installed."""
import json
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from backend.gen import django_gen, express, fastapi_gen, flask_gen, nest, spring_gen
from test_v2_phase6_integrations import STORE, _gen

GENS = {"fastapi": fastapi_gen, "flask": flask_gen, "django": django_gen, "nestjs": nest, "spring": spring_gen, "express": express}
STORAGE_FILES = {"python": ("backend/app/storage_remote.py", "backend/app/uploads_core.py"), "nestjs": ("backend/src/integrations/storage.ts", "backend/src/integrations/uploads.ts"),
                 "spring": ("backend/src/main/java/app/integrations/ObjectStore.java", "backend/src/main/java/app/integrations/UploadController.java")}


def _files(be, storage):
    spec, st, m = _gen(STORE, backend=be, cache="redis", storage=storage)
    assert m["integrations"]["uploads"] and m["storage"] == storage, (be, storage)
    return GENS[be].generate(spec, st, m)


@pytest.mark.parametrize("be", ["fastapi", "flask", "django", "nestjs", "spring"])
def test_s3_and_firebase_ship_one_store_and_the_private_upload_route(be):
    kind = "python" if be in ("fastapi", "flask", "django") else be
    for storage in ("s3", "firebase-storage"):
        f = _files(be, storage)
        assert all(k in f for k in STORAGE_FILES[kind]), (be, storage)
        text = "\n".join(f[k] for k in STORAGE_FILES[kind])
        assert "UPLOAD_DIR" not in f["backend/.env.example"] or storage == "local"
        env = f["backend/.env.example"]
        assert "UPLOAD_MAX_BYTES=" in env
        if storage == "s3":
            assert all(k in env for k in ("S3_BUCKET=", "S3_ENDPOINT=", "S3_ACCESS_KEY_ID=", "S3_SECRET_ACCESS_KEY=")) and "FIREBASE_STORAGE_BUCKET" not in env
            assert "SigV4" in f["backend/README.md"] or "Signature" in text
            assert not any(k.endswith(("FirebaseStore.java", "storage_firebase.py", "storage-firebase.ts")) for k in f)
        else:
            assert "FIREBASE_STORAGE_BUCKET=" in env and "S3_BUCKET=" not in env
            assert "Firebase Storage" in f["backend/README.md"]
            dep = f.get("backend/requirements.txt") or f.get("backend/package.json") or f["backend/pom.xml"]
            assert "firebase-admin" in dep, be
            assert not any(k.endswith(("S3Store.java", "storage_s3.py", "storage-s3.ts")) for k in f)
        assert "writeFile" not in text and "Files.write" not in text and "FileResponse" not in text and "os.open" not in text      # nothing touches the local disk
        assert not any(k.endswith(("uploads_remote.py", "uploads_remote.ts", "UploadControllerRemote.java")) for k in f)         # templates are never shipped as-is


@pytest.mark.parametrize("be", ["fastapi", "flask", "django", "nestjs", "spring"])
def test_local_storage_is_unchanged(be):
    f = _files(be, "local")
    assert not any("storage_remote" in k or k.endswith(("storage.ts", "ObjectStore.java", "S3Store.java", "FirebaseStore.java")) for k in f)
    assert "UPLOAD_DIR" in "\n".join(v for k, v in f.items() if "upload" in k.lower() or k.endswith(".env.example") or k.endswith("config.ts") or k.endswith("config.py") or k.endswith("settings.py")) or be == "spring"


def test_python_generated_files_compile():
    for be in ("fastapi", "flask", "django"):
        for storage in ("s3", "firebase-storage", "local"):
            for k, v in _files(be, storage).items():
                if k.endswith(".py"):
                    compile(v, k, "exec")


def _project(be, storage):
    d = Path(tempfile.mkdtemp())
    for k, v in _files(be, storage).items():
        (d / k).parent.mkdir(parents=True, exist_ok=True)
        (d / k).write_text(v, encoding="utf-8")
    return d / "backend"


_PNG = b"\x89PNG\r\n\x1a\n" + bytes(40)


def _fake_s3():
    store, seen = {}, []

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_PUT(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            seen.append((self.command, self.path, dict(self.headers)))
            store[self.path] = body
            self.send_response(200)
            self.end_headers()

        def do_GET(self):
            seen.append((self.command, self.path, dict(self.headers)))
            b = store.get(self.path)
            self.send_response(200 if b is not None else 404)
            self.end_headers()
            if b is not None:
                self.wfile.write(b)

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, store, seen


def test_python_s3_round_trip_against_a_fake_server():
    root = _project("fastapi", "s3")
    srv, store, seen = _fake_s3()
    sys.path.insert(0, str(root))
    try:
        import os
        os.environ.update(S3_ENDPOINT=f"http://127.0.0.1:{srv.server_port}", S3_BUCKET="bk", S3_REGION="us-east-1", S3_ACCESS_KEY_ID="AK", S3_SECRET_ACCESS_KEY="SK", JWT_SECRET="x" * 40, CORS_ORIGINS="http://localhost:5173")
        for m in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
            del sys.modules[m]
        from app import uploads_core
        from app.errors import ApiError
        out = uploads_core.save(_PNG)
        assert out["type"] == "image/png" and out["name"].endswith(".png")
        method, path, headers = seen[0]
        assert method == "PUT" and path == f"/bk/uploads/{out['name']}" and headers["Authorization"].startswith("AWS4-HMAC-SHA256 Credential=AK/")
        assert "SK" not in json.dumps(headers) and headers["Content-Type"] == "image/png"
        data, mime = uploads_core.read(out["name"])
        assert data == _PNG and mime == "image/png"
        for bad in ("../../etc/passwd", "a.png", "x" * 32 + ".exe"):
            with pytest.raises(ApiError) as e:
                uploads_core.read(bad)
            assert e.value.status == 404
        n = len(seen)
        with pytest.raises(ApiError) as e:
            uploads_core.save(b"<script>alert(1)</script>" * 3)
        assert e.value.status == 415 and len(seen) == n                       # rejected before touching the bucket
        with pytest.raises(ApiError) as e:
            uploads_core.read("a" * 32 + ".png")
        assert e.value.status == 404                                          # valid name, no such object
        from app import storage_remote
        storage_remote.cfg.s3_secret_access_key = "your-secret-access-key"
        with pytest.raises(ApiError) as e:
            uploads_core.save(_PNG)
        assert e.value.status == 503                                          # placeholder credentials: clear error, no request
    finally:
        srv.shutdown()
        sys.path.remove(str(root))
        for m in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
            del sys.modules[m]


def test_python_firebase_store_uses_the_admin_sdk_and_maps_errors():
    import types
    root = _project("fastapi", "firebase-storage")
    blobs = {}

    class Blob:
        def __init__(self, k): self.k = k
        def upload_from_string(self, b, content_type=None): blobs[self.k] = (b, content_type)
        def exists(self): return self.k in blobs
        def download_as_bytes(self): return blobs[self.k][0]

    fa = types.ModuleType("firebase_admin"); fa._apps = {}
    fa.initialize_app = lambda cred, opts: fa._apps.update(default=(cred, opts))
    cr = types.ModuleType("firebase_admin.credentials"); cr.Certificate = lambda p: ("cert", p); cr.ApplicationDefault = lambda: "adc"
    stg = types.ModuleType("firebase_admin.storage"); stg.bucket = lambda: types.SimpleNamespace(blob=Blob)
    fa.credentials, fa.storage = cr, stg
    mods = {"firebase_admin": fa, "firebase_admin.credentials": cr, "firebase_admin.storage": stg}
    sys.path.insert(0, str(root))
    try:
        import os
        os.environ.update(FIREBASE_STORAGE_BUCKET="p.appspot.com", FIREBASE_SERVICE_ACCOUNT_PATH="", JWT_SECRET="x" * 40, CORS_ORIGINS="http://localhost:5173")
        sys.modules.update(mods)
        for m in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
            del sys.modules[m]
        from app import uploads_core
        out = uploads_core.save(_PNG)
        assert blobs[f"uploads/{out['name']}"] == (_PNG, "image/png") and fa._apps["default"][0] == "adc" and fa._apps["default"][1]["storageBucket"] == "p.appspot.com"
        assert uploads_core.read(out["name"]) == (_PNG, "image/png")
    finally:
        sys.path.remove(str(root))
        for k in mods:
            sys.modules.pop(k, None)
        for m in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
            del sys.modules[m]


# Same inputs through Express (JS), Python, NestJS (TS, types stripped) and Spring (Java, static methods only): the four signatures must be identical.
_VEC = dict(method="PUT", host="bk.s3.eu-west-1.amazonaws.com", path="/uploads/a b.png", payloadHash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            amzDate="20130524T000000Z", region="eu-west-1", accessKeyId="AKIAIOSFODNN7EXAMPLE", secretAccessKey="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_all_four_signers_agree():
    d = Path(tempfile.mkdtemp())
    spec, st, m = _gen(STORE, backend="express", cache="redis", storage="s3")
    ex = express.generate(spec, st, m)
    for k in [k for k in ex if k.startswith("backend/src/") and k.endswith(".js")]:
        (d / "ex" / Path(k).relative_to("backend")).parent.mkdir(parents=True, exist_ok=True)
        (d / "ex" / Path(k).relative_to("backend")).write_text(ex[k], encoding="utf-8")
    (d / "ex" / "node_modules" / "dotenv").mkdir(parents=True)
    (d / "ex" / "node_modules" / "dotenv" / "index.js").write_text("module.exports = { config() {} };\n")      # config.js only needs it to load .env
    js = subprocess.run(["node", "-e", f"process.env.S3_ENDPOINT='https://x.test';process.env.S3_BUCKET='b';process.env.JWT_SECRET='{'x' * 40}';process.env.CORS_ORIGINS='http://a';"
                         f"console.log(require('./src/lib/s3').authorization({json.dumps(_VEC)}).header)"], cwd=d / "ex", capture_output=True, text=True)
    assert js.returncode == 0, js.stderr
    want = js.stdout.strip()
    # Python
    proot = _project("fastapi", "s3")
    sys.path.insert(0, str(proot))
    try:
        import os
        os.environ.update(JWT_SECRET="x" * 40, CORS_ORIGINS="http://localhost:5173")
        for k in [k for k in sys.modules if k == "app" or k.startswith("app.")]:
            del sys.modules[k]
        from app import storage_remote
        got, _ = storage_remote.authorization(_VEC["method"], _VEC["host"], _VEC["path"], _VEC["payloadHash"], _VEC["amzDate"], _VEC["region"], _VEC["accessKeyId"], _VEC["secretAccessKey"])
        assert got == want
    finally:
        sys.path.remove(str(proot))
        for k in [k for k in sys.modules if k == "app" or k.startswith("app.")]:
            del sys.modules[k]
    # NestJS: transpile the generated module with the TypeScript compiler (when installed) and run it against a stub config
    tsc = shutil.which("tsc")
    if tsc:
        nf = _files("nestjs", "s3")["backend/src/integrations/storage.ts"]
        (d / "nest" / "integrations").mkdir(parents=True)
        (d / "nest" / "config.js").write_text("exports.cfg = { s3: { endpoint: 'https://x.test', bucket: 'b', region: 'eu-west-1', accessKeyId: 'a', secretAccessKey: 'b' } };\n")
        (d / "nest" / "integrations" / "storage.ts").write_text(nf)
        ts_dir = Path(tsc).resolve().parent.parent
        code = (f"const ts=require({json.dumps(str(ts_dir))});const fs=require('fs');"
                "const o=ts.transpileModule(fs.readFileSync('integrations/storage.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText;"
                "fs.writeFileSync('integrations/storage.js',o);"
                f"console.log(require('./integrations/storage').authorization({json.dumps(_VEC)}).header)")
        r = subprocess.run(["node", "-e", code], cwd=d / "nest", capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert r.stdout.strip() == want
    # Spring: compile and run the static signer alone when a JDK is present
    if shutil.which("java"):
        src = _files("spring", "s3")["backend/src/main/java/app/integrations/S3Store.java"]
        a, b = src.index("    static byte[] hmac"), src.index("    /** AWS endpoints use")
        v = _VEC
        prog = ("import java.nio.charset.StandardCharsets;import java.net.URLEncoder;import java.security.MessageDigest;import java.util.*;import javax.crypto.Mac;import javax.crypto.spec.SecretKeySpec;\n"
                "public class Sig {\n" + src[a:b] + f'    public static void main(String[] x) {{ System.out.println(authorization("{v["method"]}", "{v["host"]}", "{v["path"]}", "{v["payloadHash"]}", "{v["amzDate"]}", "{v["region"]}", "{v["accessKeyId"]}", "{v["secretAccessKey"]}")); }}\n}}\n')
        (d / "Sig.java").write_text(prog)
        j = subprocess.run(["java", "Sig.java"], cwd=d, capture_output=True, text=True)
        if j.returncode != 0 and "compiler" in j.stderr.lower():
            return                                                # a JRE without the compiler module
        assert j.returncode == 0, j.stderr
        assert j.stdout.strip() == want
