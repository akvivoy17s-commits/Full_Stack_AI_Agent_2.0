import hashlib
import json
from types import SimpleNamespace

from backend.engines.html2jsx import convert as html_to_jsx
from backend.engines.react_engine import (
    _normalize_firebase_auth_form_jsx, _normalize_firebase_auth_form_tags, _wire_firebase_auth_form,
)
from backend.gen import firebase_client
from backend.stack import catalog
from backend.stack.resolver import readiness


class FakeProjectFiles:
    def __init__(self):
        self.files = {
            "package.json": json.dumps({
                "name": "generated-site", "private": True, "version": "0.1.0", "type": "module",
                "scripts": {"build": "tsc --noEmit && vite build"},
                "dependencies": {"react": "^18.3.1", "react-dom": "^18.3.1"},
                "devDependencies": {"vite": "^5.4.0", "typescript": "^5.5.4"},
            }),
            ".env.example": "VITE_APP_TITLE=Demo\n",
            ".gitignore": "node_modules\ndist\n",
        }

    def read(self, path):
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def write(self, path, content):
        self.files[path] = content
        return self.hash(path)

    def hash(self, path):
        return hashlib.md5(self.files[path].encode()).hexdigest()[:8]

    def tree(self):
        return sorted(self.files)


def _state(auth="none", database="firestore", deploy="firebase-hosting"):
    return SimpleNamespace(stack_config={"stack": {
        "frontend": "react", "frontend_lang": "ts", "backend": "none",
        "database": database, "auth": auth, "deploy": deploy,
    }})


def test_firebase_stack_is_ready_not_reported_as_planned():
    cfg = _state(auth="firebase-auth").stack_config["stack"]
    result = readiness(cfg)
    assert result["blocking"] == []
    assert not result["pending"]
    assert catalog.status("database", "firestore", cfg) == "ready"
    assert catalog.status("auth", "firebase-auth", cfg) == "ready"
    assert catalog.status("deploy", "firebase-hosting", cfg) == "ready"


def test_generator_emits_firestore_hosting_auth_and_env_template():
    pf = FakeProjectFiles()
    result = firebase_client.run(pf, _state(auth="none"))
    assert result["generated"]
    assert "firebase" in json.loads(pf.files["package.json"])["dependencies"]
    assert "VITE_FIREBASE_PROJECT_ID=" in pf.files[".env.example"]
    firebase_json = json.loads(pf.files["firebase.json"])
    assert firebase_json["hosting"]["public"] == "dist"
    assert firebase_json["firestore"]["rules"] == "firestore.rules"
    assert "ALLOW_ANONYMOUS_AUTH = true" in pf.files["src/lib/firebaseData.ts"]
    assert "ownerUid" in pf.files["firestore.rules"]
    assert "src/components/FirebaseAuthBridge.tsx" not in pf.files
    assert "serviceAccount" not in pf.files["src/lib/firebase.ts"]


def test_explicit_firebase_auth_disables_anonymous_fallback():
    pf = FakeProjectFiles()
    firebase_client.run(pf, _state(auth="firebase-auth", deploy="local"))
    assert "ALLOW_ANONYMOUS_AUTH = false" in pf.files["src/lib/firebaseData.ts"]
    assert "src/components/FirebaseAuthBridge.tsx" in pf.files
    assert "hosting" not in json.loads(pf.files["firebase.json"])


def test_auth_only_stack_does_not_generate_firestore_rules():
    pf = FakeProjectFiles()
    result = firebase_client.run(pf, _state(auth="firebase-auth", database="none", deploy="local"))
    assert result["generated"]
    assert "src/lib/firebaseData.ts" not in pf.files
    assert "firestore.rules" not in pf.files
    assert "firebase.json" not in pf.files
    assert "src/components/FirebaseAuthBridge.tsx" in pf.files


def test_register_form_tags_name_email_and_password_correctly():
    html = '<form><input placeholder="Full name"><input placeholder="Email"><input type="password"><button>Register</button></form>'
    result = _wire_firebase_auth_form(html, "register")
    assert 'data-firebase-auth="register"' in result
    assert '<input placeholder="Full name" name="fullName">' in result
    assert '<input type="email" placeholder="Email" name="email">' in result
    assert 'name="password"' in result
    assert 'data-firebase-auth-status' in result


def test_auth_form_fallback_sets_email_for_plain_text_input():
    html = '<form><input type="text"><input type="password"><button>Login</button></form>'
    result = _wire_firebase_auth_form(html, "login")
    assert '<input type="text" name="email">' in result
    assert '<input type="password" name="password">' in result


def test_non_firebase_stack_is_not_claimed_by_client_generator():
    cfg = {"frontend": "react", "frontend_lang": "ts", "backend": "none", "database": "sqlite", "auth": "none", "deploy": "local"}
    assert not firebase_client.applies(cfg)


def test_firebase_auth_pseudo_component_is_normalized_before_jsx_conversion():
    source = '<FirebaseAuthForm class="auth-form"><input type="email"><input type="password"></FirebaseAuthForm>'
    normalized = _normalize_firebase_auth_form_tags(source, "login")
    wired = _wire_firebase_auth_form(normalized, "login")
    jsx = html_to_jsx(wired)

    assert "FirebaseAuthForm" not in jsx
    assert "firebaseauthform" not in jsx.lower()
    assert '<form' in jsx
    assert 'data-firebase-auth="login"' in jsx
    assert 'data-firebase-auth-status' in jsx


def test_firebase_auth_pseudo_component_is_normalized_after_conversion_too():
    jsx = '<><FirebaseAuthForm className="auth-form"><input /></FirebaseAuthForm></>'
    normalized = _normalize_firebase_auth_form_jsx(jsx, "register")

    assert "FirebaseAuthForm" not in normalized
    assert "firebaseauthform" not in normalized.lower()
    assert '<form className="auth-form" data-firebase-auth="register">' in normalized
    assert "</form>" in normalized
