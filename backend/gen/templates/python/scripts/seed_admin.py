"""Creates the first admin from ADMIN_EMAIL / ADMIN_PASSWORD: python -m scripts.seed_admin
Public sign-up can never create an admin."""
import os
import sys

from app import schema
from app.config import cfg
from app.db import connect
from app.security import hash_password
from app.validation import EMAIL, now_iso

if __name__ == "__main__":
    try:
        cfg.validate()
        email, pw = os.environ.get("ADMIN_EMAIL", "").strip().lower(), os.environ.get("ADMIN_PASSWORD", "")
        if not EMAIL.match(email) or not 8 <= len(pw) or len(pw.encode()) > 72 or pw.startswith("<"):
            raise RuntimeError("Set ADMIN_EMAIL and ADMIN_PASSWORD (8-72 characters) in .env first")
        db = connect()
        db.migrate()
        if db.find_one("User", {"email": email}):
            print("That account already exists; nothing changed.")
        else:
            data = {"email": email, "name": "Administrator", "password_hash": hash_password(pw), "role": schema.SCHEMA["adminRole"]}
            if any(f["name"] == "created_at" for f in schema.SCHEMA["entities"]["User"]["fields"]):
                data["created_at"] = now_iso()
            db.create("User", data)
            print(f"Admin created: {email}")
        db.close()
    except Exception as exc:  # readable message instead of a traceback for setup mistakes
        print(f"Seed failed: {exc}", file=sys.stderr)
        sys.exit(1)
