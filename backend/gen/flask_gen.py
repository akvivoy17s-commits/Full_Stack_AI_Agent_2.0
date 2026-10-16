"""Flask (Python) generator. Same framework-neutral core as FastAPI (templates/python); only the web layer (templates/flask) differs."""
from backend.gen import fastapi_gen as F

ROOTS = (F.ROOT / "python", F.ROOT / "flask")
BASE = ["flask>=3.0,<4", "waitress>=3.0,<4", "python-dotenv>=1.0,<2"]
LABEL = "Flask"
commands = F.commands
env_lines = F.env_lines


def requirements(m: dict, dev: bool = False) -> str:
    return F.requirements(m, dev, BASE)


def readme(m: dict, spec: dict) -> str:
    return F.readme(m, spec, LABEL)


def generate(spec: dict, stack: dict, m: dict) -> dict[str, str]:
    files = F.generate(spec, stack, m, key="flask", roots=ROOTS, base=BASE, label=LABEL)
    if "backend/README.md" in files:   # Flask has no built-in interactive docs: /api/docs is a generated route reference
        files["backend/README.md"] = files["backend/README.md"].replace("API docs: /api/docs", "route reference: /api/docs")
    return files
