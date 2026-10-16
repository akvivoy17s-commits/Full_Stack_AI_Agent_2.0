"""Optional sample data for development: python -m scripts.seed_sample
Inserts a few obviously-fake rows per entity (from app/schema.py). Safe to run twice: an entity that already has rows is left alone.
Records that point at User are linked to the admin created by `python -m scripts.seed_admin`; run that first if the app has sign-in."""
import os
import sys

from app import schema
from app.config import cfg
from app.db import connect
from app.validation import parse_dt

if __name__ == "__main__":
    try:
        cfg.validate()
        if cfg.env == "production" and os.environ.get("ALLOW_SAMPLE_DATA") != "true":
            raise RuntimeError("Refusing to add sample data in production (set ALLOW_SAMPLE_DATA=true to override)")
        db = connect()
        db.migrate()
        ids, done = {}, 0
        admin = db.find_one("User", {"email": os.environ.get("ADMIN_EMAIL", "").strip().lower()}) if schema.SCHEMA["auth"] else None
        if admin:
            ids["User"] = [admin["id"]]
        for plan in schema.SCHEMA["seed"]:
            name, ent = plan["entity"], schema.SCHEMA["entities"][plan["entity"]]
            page = db.list_page(name, 1, 100, "", {}, {})
            if page["total"]:                         # keep what is there and let later entities point at it
                ids[name] = sorted(r["id"] for r in page["rows"])[:3]
                print(f"Skipped {name}: it already has data.")
                continue
            refs = {v["$ref"][0] for r in plan["rows"] for v in r.values() if isinstance(v, dict)}
            if "User" in refs and not admin:
                print(f"Skipped {name}: it points at a user; run `python -m scripts.seed_admin` first.")
                continue
            if refs - set(ids):
                print(f"Skipped {name}: it needs {', '.join(sorted(refs - set(ids)))} records first.")
                continue
            kinds, made = {f["name"]: f["type"] for f in ent["fields"]}, []
            for row in plan["rows"]:
                data = {}
                for k, v in row.items():
                    if isinstance(v, dict):
                        parent, idx = v["$ref"]
                        v = ids[parent][idx]
                    elif kinds[k] == "datetime":
                        v = parse_dt(v)
                    data[k] = v
                made.append(db.create(name, data)["id"])
            ids[name] = made
            done += 1
            print(f"Added {len(made)} {name} record(s).")
        db.close()
        print("Sample data is ready." if done else "Nothing to add.")
    except Exception as exc:  # readable message instead of a traceback for setup mistakes
        print(f"Seed failed: {exc}", file=sys.stderr)
        sys.exit(1)
