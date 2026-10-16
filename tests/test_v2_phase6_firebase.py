"""Phase 6G: Express + Firebase (ID-token sign-in, Firebase Storage uploads). Pure Python; node runs when installed."""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from backend.gen import express, model
from backend.spec import compose
from gen_helpers import stack_for

BRIEF = "online store with products cart and orders, image uploads, firebase authentication and firebase storage"
PLAIN = "college management system with student login and courses"


def _gen(brief=BRIEF, db="sqlite", **extra):
    st = stack_for(db, brief, backend="express", **extra)
    spec = compose.build(brief, st)
    m = model.build(spec, st)
    return spec, st, m, express.generate(spec, st, m)


def _node_check(files):
    if not shutil.which("node"):
        return
    with tempfile.TemporaryDirectory() as d:
        for rel, txt in files.items():
            if rel.endswith(".js"):
                p = Path(d) / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(txt, encoding="utf-8")
                r = subprocess.run(["node", "--check", str(p)], capture_output=True, text=True)
                assert r.returncode == 0, (rel, r.stderr)


def test_firebase_auth_and_storage_generated():
    spec, st, m, files = _gen(auth="firebase-auth", storage="firebase-storage")
    assert m["firebaseAuth"] is True and m["storage"] == "firebase-storage" and m["integrations"]["uploads"]
    assert "POST /api/auth/firebase" in m["manifest"]
    for f in ("lib/firebase.js", "routes/uploads.js", "routes/auth.js"):
        assert f"backend/src/{f}" in files
    up = files["backend/src/routes/uploads.js"]
    assert "lib/firebase" in up and "store.put(" in up and "s3" not in up.replace("S3", "")  # no leftover S3 calls
    assert json.loads(files["backend/package.json"])["dependencies"]["firebase-admin"]
    env = files["backend/.env.example"]
    for k in ("FIREBASE_PROJECT_ID=", "FIREBASE_SERVICE_ACCOUNT_PATH=", "FIREBASE_STORAGE_BUCKET="):
        assert k in env
    assert "secrets/" in files["backend/.gitignore"]
    assert "/api/auth/firebase" in json.loads(files["backend/openapi.json"])["paths"]
    assert '"firebaseAuth": true' in files["backend/src/schema.js"]
    assert "Firebase sign-in" in files["backend/README.md"] and "Firebase Storage" in files["backend/README.md"]
    _node_check(files)


def test_storage_only_has_no_firebase_sign_in():
    spec, st, m, files = _gen(auth="jwt", storage="firebase-storage")
    assert m["firebaseAuth"] is False and "POST /api/auth/firebase" not in m["manifest"]
    assert "backend/src/lib/firebase.js" in files and "FIREBASE_STORAGE_BUCKET=" in files["backend/.env.example"]
    assert "/api/auth/firebase" not in json.loads(files["backend/openapi.json"])["paths"]
    _node_check(files)


def test_plain_app_ships_no_firebase():
    spec, st, m, files = _gen(PLAIN)
    assert m["firebaseAuth"] is False
    assert "backend/src/lib/firebase.js" not in files
    assert "firebase-admin" not in files["backend/package.json"] and "FIREBASE" not in files["backend/.env.example"]


def test_other_storage_modes_unchanged():
    _, _, m, files = _gen(auth="jwt", storage="s3")
    assert m["storage"] == "s3" and "backend/src/lib/s3.js" in files and "backend/src/lib/firebase.js" not in files


NODE_UNIT = r"""
const Module = require('module'); const assert = require('assert'); const path = require('path');
const root = process.argv[2];
const calls = []; let mode = 'ok';
const fakeAdmin = { apps: [], credential: { cert: (j) => ({ cert: j }), applicationDefault: () => ({ adc: true }) },
  initializeApp(o) { calls.push(o); this.apps.push(o); },
  auth: () => ({ verifyIdToken: async (t, rev) => { if (t === 'bad') throw new Error('x'); return { email: 'a@b.co', email_verified: true, rev }; } }),
  storage: () => ({ bucket: () => ({ file: (k) => ({ save: async (b, o) => { if (mode === 'fail') throw new Error('boom'); calls.push(['save', k, o]); },
    download: async () => { if (mode === 'missing') { const e = new Error('nf'); e.code = 404; throw e; } return [Buffer.from('hi')]; } }) }) }) };
const orig = Module._load;
Module._load = function (req, parent, ...r) {
  if (req === 'firebase-admin') return fakeAdmin;
  if (req === '../config') return { firebase: { projectId: 'p', serviceAccountPath: '', storageBucket: 'b' } };
  return orig.call(this, req, parent, ...r);
};
const fb = require(path.join(root, 'src/lib/firebase.js'));
(async () => {
  assert.equal((await fb.verifyIdToken('good')).rev, true);                         // revocation check on
  await assert.rejects(fb.verifyIdToken('bad'));
  assert.deepEqual(calls[0], { credential: { adc: true }, projectId: 'p', storageBucket: 'b' });
  await fb.storage.put('k.png', Buffer.from('x'), 'image/png');
  assert.deepEqual(calls[1], ['save', 'k.png', { contentType: 'image/png', resumable: false }]);
  assert.equal((await fb.storage.get('k.png')).toString(), 'hi');
  mode = 'missing'; assert.equal(await fb.storage.get('k.png'), null);
  mode = 'fail'; await assert.rejects(fb.storage.put('k', Buffer.from('x'), 'a/b'), (e) => e.status === 502 || e.statusCode === 502);
  console.log('OK');
})().catch((e) => { console.error(e); process.exit(1); });
"""


def test_firebase_lib_runs_against_stub_sdk():
    if not shutil.which("node"):
        return
    spec, st, m, files = _gen(auth="firebase-auth", storage="firebase-storage")
    with tempfile.TemporaryDirectory() as d:
        for rel in ("src/lib/firebase.js", "src/lib/http.js"):
            p = Path(d) / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(files["backend/" + rel], encoding="utf-8")
        (Path(d) / "unit.js").write_text(NODE_UNIT, encoding="utf-8")
        r = subprocess.run(["node", "unit.js", d], capture_output=True, text=True, cwd=d)
        assert r.returncode == 0 and "OK" in r.stdout, r.stdout + r.stderr
