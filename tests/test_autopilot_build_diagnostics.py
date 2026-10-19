from types import SimpleNamespace

from backend.engines import react_engine
from backend.tools.terminal import _clip_output
from backend.agent.llm import _stream_read_timeout


def test_terminal_clip_keeps_both_error_header_and_stack_tail():
    source = "START OF BUILD\n" + ("ordinary line\n" * 1000) + "Rollup stack tail\n"
    clipped = _clip_output(source, 300)
    assert len(clipped) <= 300
    assert clipped.startswith("START OF BUILD")
    assert clipped.endswith("Rollup stack tail\n")
    assert "output truncated" in clipped


def test_diagnostic_blocks_keep_typescript_path_and_error():
    out = """vite v5.4.0 building for production...
transforming...
✓ 13 modules transformed.
error during build:
[vite:esbuild] Transform failed with 1 error:
C:/app/generated/src/sections/Charts.tsx:6:27: ERROR: Unexpected token
    at failureErrorWithLog (node_modules/esbuild/lib/main.js:123:15)
"""
    blocks = react_engine.diagnostic_blocks(out)
    full = "\n".join(blocks)
    assert "src/sections/Charts.tsx:6:27" in full
    assert "Unexpected token" in full
    assert react_engine.sid_from_output(full, SimpleNamespace(plan={"sections": ["charts", "overview"]})) == "charts"


def test_stream_read_timeout_uses_configured_deadline_but_is_bounded():
    assert _stream_read_timeout({"timeout_s": 3600}) == 300
    assert _stream_read_timeout({"timeout_s": 90}) == 90
    assert _stream_read_timeout({"timeout_s": 10}) == 10
