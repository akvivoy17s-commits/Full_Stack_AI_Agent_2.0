"""Generate a browser-safe Firebase client integration for React + TypeScript projects.

The Firebase Web API key and project identifiers are public client configuration, not
server secrets. Data authorization is enforced by Firestore security rules; private
service-account credentials must never be emitted to a Vite frontend.
"""
from __future__ import annotations

import json
import re

FIREBASE_DB_VALUES = {"firestore"}

ENV_EXAMPLE = """# Firebase Web app configuration (public by design; protect data with Firebase Security Rules)
VITE_FIREBASE_API_KEY=your-firebase-web-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project-id.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=your-messaging-sender-id
VITE_FIREBASE_APP_ID=your-firebase-app-id
VITE_FIREBASE_DATABASE_URL=https://your-project-id-default-rtdb.firebaseio.com
"""

FIREBASE_TS = r'''import { getApp, getApps, initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'
import { getFirestore } from 'firebase/firestore'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || '',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || '',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || '',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || '',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '',
  databaseURL: import.meta.env.VITE_FIREBASE_DATABASE_URL || undefined,
}

const missing = ['apiKey', 'authDomain', 'projectId', 'appId'].filter((key) => !firebaseConfig[key as keyof typeof firebaseConfig])
if (missing.length) {
  console.warn(`Firebase configuration is incomplete. Set VITE_FIREBASE_${missing.map((key) => key.replace(/[A-Z]/g, (m) => `_${m}`).toUpperCase()).join(', VITE_FIREBASE_')} in the project .env file.`)
}

export const firebaseApp = getApps().length ? getApp() : initializeApp(firebaseConfig)
export const auth = getAuth(firebaseApp)
export const db = getFirestore(firebaseApp)
'''

FIRESTORE_DATA_TS = r'''import { signInAnonymously } from 'firebase/auth'
import {
  addDoc, collection, deleteDoc, doc, getDocs, query, serverTimestamp, updateDoc, where,
} from 'firebase/firestore'
import { auth, db } from './firebase'

type DataRecord = Record<string, unknown> & { id: string }
const ALLOW_ANONYMOUS_AUTH = __ALLOW_ANONYMOUS_AUTH__
let anonymousSignInPromise: Promise<string> | null = null

async function currentUid(): Promise<string> {
  const uid = auth.currentUser?.uid
  if (uid) return uid
  if (!ALLOW_ANONYMOUS_AUTH) throw new Error('Please sign in before accessing saved data.')
  if (anonymousSignInPromise) return anonymousSignInPromise
  const pending = signInAnonymously(auth).then((credential) => credential.user.uid)
    .finally(() => { anonymousSignInPromise = null })
  anonymousSignInPromise = pending
  return pending
}

function safeCollectionName(value: string): string {
  const name = String(value || '').trim()
  if (!/^[a-zA-Z][a-zA-Z0-9_-]{0,49}$/.test(name)) throw new Error('Invalid collection name.')
  return name
}

export async function listOwnedDocuments(collectionName: string): Promise<DataRecord[]> {
  const uid = await currentUid()
  const ref = collection(db, safeCollectionName(collectionName))
  const snap = await getDocs(query(ref, where('ownerUid', '==', uid)))
  return snap.docs.map((item) => ({ ...item.data(), id: item.id } as DataRecord))
}

export async function createOwnedDocument(collectionName: string, value: Record<string, unknown>): Promise<string> {
  const uid = await currentUid()
  const ref = collection(db, safeCollectionName(collectionName))
  const created = await addDoc(ref, { ...value, ownerUid: uid, createdAt: serverTimestamp(), updatedAt: serverTimestamp() })
  return created.id
}

export async function updateOwnedDocument(collectionName: string, id: string, value: Record<string, unknown>): Promise<void> {
  const uid = await currentUid()
  if (!id || id.includes('/')) throw new Error('Invalid document id.')
  await updateDoc(doc(db, safeCollectionName(collectionName), id), { ...value, ownerUid: uid, updatedAt: serverTimestamp() })
}

export async function deleteOwnedDocument(collectionName: string, id: string): Promise<void> {
  await currentUid()
  if (!id || id.includes('/')) throw new Error('Invalid document id.')
  await deleteDoc(doc(db, safeCollectionName(collectionName), id))
}
'''

FIREBASE_AUTH_BRIDGE = r'''import { useEffect } from 'react'
import {
  createUserWithEmailAndPassword, onAuthStateChanged, sendPasswordResetEmail,
  signInWithEmailAndPassword, updatePassword, updateProfile,
} from 'firebase/auth'
import { auth } from '../lib/firebase'

function showStatus(form: HTMLFormElement, message: string, isError = false) {
  let node = form.querySelector<HTMLElement>('[data-firebase-auth-status]')
  if (!node) {
    node = document.createElement('p')
    node.dataset.firebaseAuthStatus = 'true'
    node.setAttribute('aria-live', 'polite')
    form.appendChild(node)
  }
  node.textContent = message
  node.setAttribute('role', isError ? 'alert' : 'status')
  node.style.color = isError ? '#dc2626' : 'inherit'
}

export default function FirebaseAuthBridge() {
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      document.documentElement.dataset.firebaseSignedIn = user ? 'true' : 'false'
      document.documentElement.dataset.firebaseUserEmail = user?.email || ''
    })
    const submit = async (event: Event) => {
      const form = event.target
      if (!(form instanceof HTMLFormElement)) return
      const mode = form.dataset.firebaseAuth
      if (!mode) return
      event.preventDefault()
      const values = new FormData(form)
      const emailInput = form.querySelector<HTMLInputElement>('input[type="email"], input[name="email"], input[autocomplete="email"]')
      const passwordInput = form.querySelector<HTMLInputElement>('input[type="password"], input[name="password"]')
      const email = String(values.get('email') || emailInput?.value || '').trim()
      const password = String(values.get('password') || passwordInput?.value || '')
      const name = String(values.get('name') || values.get('fullName') || form.querySelector<HTMLInputElement>('input[autocomplete="name"], input[name="name"], input[name="fullName"]')?.value || '').trim()
      const submitButton = form.querySelector<HTMLButtonElement>('button[type="submit"], input[type="submit"]')
      if (submitButton) submitButton.disabled = true
      try {
        if (mode === 'forgot_password') {
          if (!email) throw new Error('Enter your email address first.')
          await sendPasswordResetEmail(auth, email)
          showStatus(form, 'Password reset email sent. Check your inbox.')
        } else if (mode === 'reset_password') {
          if (!password) throw new Error('Enter a new password.')
          if (!auth.currentUser) throw new Error('Sign in again before changing your password, or use Forgot password.')
          await updatePassword(auth.currentUser, password)
          showStatus(form, 'Password updated successfully.')
        } else if (mode === 'register') {
          if (!email || !password) throw new Error('Enter both email and password.')
          const credential = await createUserWithEmailAndPassword(auth, email, password)
          if (name) await updateProfile(credential.user, { displayName: name })
          showStatus(form, 'Account created successfully.')
          form.dispatchEvent(new CustomEvent('firebase-auth-success', { bubbles: true, detail: { mode, uid: credential.user.uid } }))
        } else {
          if (!email || !password) throw new Error('Enter both email and password.')
          const credential = await signInWithEmailAndPassword(auth, email, password)
          showStatus(form, 'Signed in successfully.')
          form.dispatchEvent(new CustomEvent('firebase-auth-success', { bubbles: true, detail: { mode, uid: credential.user.uid } }))
        }
      } catch (error) {
        const code = String((error as { code?: string })?.code || '')
        const friendly: Record<string, string> = {
          'auth/invalid-credential': 'Email or password is incorrect.',
          'auth/user-not-found': 'No account was found for this email.',
          'auth/email-already-in-use': 'An account already exists for this email.',
          'auth/weak-password': 'Choose a stronger password (at least 6 characters).',
          'auth/invalid-email': 'Enter a valid email address.',
          'auth/network-request-failed': 'Network error. Check your connection and try again.',
          'auth/too-many-requests': 'Too many attempts. Please try again later.',
        }
        showStatus(form, friendly[code] || (error instanceof Error ? error.message : 'Authentication failed.'), true)
      } finally {
        if (submitButton) submitButton.disabled = false
      }
    }
    document.addEventListener('submit', submit, true)
    return () => {
      unsubscribe()
      document.removeEventListener('submit', submit, true)
      delete document.documentElement.dataset.firebaseSignedIn
      delete document.documentElement.dataset.firebaseUserEmail
    }
  }, [])
  return null
}
'''

FIRESTORE_RULES = '''rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // User-owned top-level documents. The generated CRUD helper always writes ownerUid.
    match /{collectionName}/{documentId} {
      allow get, list: if request.auth != null && resource.data.ownerUid == request.auth.uid;
      allow create: if request.auth != null && request.resource.data.ownerUid == request.auth.uid;
      allow update: if request.auth != null
                    && resource.data.ownerUid == request.auth.uid
                    && request.resource.data.ownerUid == request.auth.uid;
      allow delete: if request.auth != null && resource.data.ownerUid == request.auth.uid;
    }
    // Deny everything else by default, including nested collections until rules are designed.
    match /{path=**} {
      allow read, write: if false;
    }
  }
}
'''

FIREBASE_JSON = '''{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "cleanUrls": true,
    "rewrites": [{ "source": "**", "destination": "/index.html" }]
  },
  "firestore": { "rules": "firestore.rules" }
}
'''

FIREBASE_RC_EXAMPLE = '''{
  "projects": {
    "default": "YOUR_FIREBASE_PROJECT_ID"
  }
}
'''

FIREBASE_SETUP = '''# Firebase setup for this generated project

1. Create or open a Firebase project and register a **Web app**.
2. Copy the Web app's config values into this project's `.env` using the `VITE_FIREBASE_*` names in `.env.example`.
3. In Firebase Console → Authentication → Sign-in method, enable Email/Password when this project uses Firebase Authentication.
4. Create a Cloud Firestore database when this project uses Firestore.
5. Review `firestore.rules`. These generated rules intentionally default-deny data and only permit signed-in users to read/write their own top-level documents carrying `ownerUid`.
6. If the app uses Firestore without a visible Firebase Authentication sign-in flow, enable the **Anonymous** sign-in provider; the generated data helper uses anonymous accounts to enforce per-user owner rules. Run `npm install` and `npm run build` before testing. Do not paste a service-account private key or other server secret into any `VITE_*` variable.
7. For Firebase Hosting, copy `.firebaserc.example` to `.firebaserc`, replace the project ID, then run `npm install -g firebase-tools`, `firebase login`, `firebase deploy --only hosting` (and `firestore:rules` when Firestore is used).

Firebase Web config (including the Web API key) is browser-visible configuration. It is not an authorization boundary. Use Authentication, Firestore rules, and App Check as appropriate. The agent generates configuration files; it does not create your Firebase project, enable services, or deploy automatically.
'''


def applies(stack: dict | None) -> bool:
    stack = stack or {}
    return (
        stack.get("frontend") == "react"
        and stack.get("frontend_lang") == "ts"
        and (stack.get("backend") or "none") == "none"
        and (
            (stack.get("database") or "none") in FIREBASE_DB_VALUES
            or (stack.get("auth") or "none") == "firebase-auth"
            or (stack.get("deploy") or "none") == "firebase-hosting"
        )
    )


def _merge_env(existing: str) -> str:
    lines = [ln for ln in existing.splitlines() if ln.strip()]
    present = {ln.split("=", 1)[0].strip() for ln in lines if "=" in ln and not ln.lstrip().startswith("#")}
    additions = []
    for line in ENV_EXAMPLE.splitlines():
        key = line.split("=", 1)[0].strip() if "=" in line else ""
        if key and key not in present:
            additions.append(line)
            present.add(key)
    if not lines:
        return ENV_EXAMPLE
    if not additions:
        return existing.rstrip() + "\n"
    return existing.rstrip() + "\n\n# Firebase browser configuration (public values; secure data using rules)\n" + "\n".join(additions) + "\n"


def run(pf, state) -> dict:
    """Generate Firebase client files without overwriting files already customized by the user."""
    stack = ((getattr(state, "stack_config", None) or {}).get("stack") or {})
    if not applies(stack):
        return {"generated": False, "files": [], "note": "Firebase client generator does not apply to this stack."}
    written = []
    try:
        package = json.loads(pf.read("package.json"))
    except (OSError, ValueError):
        package = {"name": "generated-site", "private": True, "version": "0.1.0", "type": "module", "scripts": {"dev": "vite", "build": "tsc --noEmit && vite build", "preview": "vite preview"}, "dependencies": {"react": "^18.3.1", "react-dom": "^18.3.1"}, "devDependencies": {"typescript": "^5.5.4", "vite": "^5.4.0"}}
    dependencies = package.setdefault("dependencies", {})
    if "firebase" not in dependencies:
        dependencies["firebase"] = "^11.0.0"
        pf.write("package.json", json.dumps(package, indent=2) + "\n")
        written.append("package.json")
    try:
        old_env = pf.read(".env.example")
    except (OSError, ValueError):
        old_env = ""
    env = _merge_env(old_env)
    if env != old_env:
        pf.write(".env.example", env)
        written.append(".env.example")

    db = stack.get("database") or "none"
    auth_selected = (stack.get("auth") or "none") == "firebase-auth"
    deploy_selected = (stack.get("deploy") or "none") == "firebase-hosting"
    files = {
        "src/lib/firebase.ts": FIREBASE_TS,
        "src/components/FirebaseAuthBridge.tsx": FIREBASE_AUTH_BRIDGE,
        ".firebaserc.example": FIREBASE_RC_EXAMPLE,
        "FIREBASE_SETUP.md": FIREBASE_SETUP,
    }
    if db in FIREBASE_DB_VALUES:
        files["src/lib/firebaseData.ts"] = FIRESTORE_DATA_TS.replace(
            "__ALLOW_ANONYMOUS_AUTH__", "false" if auth_selected else "true"
        )
        files["firestore.rules"] = FIRESTORE_RULES
    firebase_json = {}
    if deploy_selected:
        firebase_json["hosting"] = json.loads(FIREBASE_JSON)["hosting"]
    if db in FIREBASE_DB_VALUES:
        firebase_json["firestore"] = {"rules": "firestore.rules"}
    if firebase_json:
        files["firebase.json"] = json.dumps(firebase_json, indent=2) + "\n"
    if not auth_selected:
        files.pop("src/components/FirebaseAuthBridge.tsx", None)
    for rel, content in files.items():
        try:
            current = pf.read(rel)
        except (OSError, ValueError):
            current = None
        if current is None:
            pf.write(rel, content)
            written.append(rel)

    # Ensure generated credentials are examples only; keep real .env files outside agent writes.
    try:
        ignore = pf.read(".gitignore")
    except (OSError, ValueError):
        ignore = "node_modules\ndist\n"
    rows = [line for line in ignore.splitlines() if line not in (".env", ".env.*", "!.env.example")]
    rows += [".env", ".env.*", "!.env.example"]
    next_ignore = "\n".join(dict.fromkeys(rows)).rstrip() + "\n"
    if next_ignore != ignore:
        pf.write(".gitignore", next_ignore)
        written.append(".gitignore")

    return {"generated": True, "files": written, "firebase_database": db if db in FIREBASE_DB_VALUES else "none",
            "firebase_auth": auth_selected, "hosting_config": deploy_selected,
            "note": "Firebase client scaffolding created. Configure the public VITE_FIREBASE_* values, enable Anonymous auth when Firestore is used without a sign-in UI, deploy the Firestore rules, and configure the Firebase project before use."}
