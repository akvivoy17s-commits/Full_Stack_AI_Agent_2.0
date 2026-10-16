import os
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp(prefix="fae-test-")          # isolate DB + generated projects from real data
os.environ["DATA_DIR"] = str(Path(_tmp) / "data")
os.environ["GENERATED_DIR"] = str(Path(_tmp) / "gen")
os.environ["MOCK_LLM"] = "1"
os.environ["USE_BROWSER"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))      # shared test helpers (gen_helpers.py)
