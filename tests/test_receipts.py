#!/usr/bin/env python3
"""Unit tests for scripts/receipts.py — no network, no tools. Self-running: prints OK."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import receipts  # noqa: E402


def test_python_passthrough_detection():
    assert receipts.classify_match("a.py", "def f(a, b):\n    return g(a, b)\n")["passthrough"] is True
    assert receipts.classify_match("a.py", 'def f(a, b):\n    """doc"""\n    return g(a, b)\n')["passthrough"] is True
    assert receipts.classify_match("a.py", "def f(a, b):\n    return g(b=b, a=a)\n")["passthrough"] is True
    assert receipts.classify_match("a.py", "def f(*args, **kw):\n    return g(*args, **kw)\n")["passthrough"] is True
    assert receipts.classify_match("a.py", "def f(self, x):\n    return self.inner.f(x)\n")["passthrough"] is True
    assert receipts.classify_match("a.py", "def f(a):\n    return g(a + 1)\n")["passthrough"] is False
    assert receipts.classify_match("a.py", "def f(a, b):\n    return g(a)\n")["passthrough"] is False
    assert receipts.classify_match("a.py", "def f(a):\n    return cls(verified=a, other=1)\n")["passthrough"] is False
    assert receipts.classify_match("a.py", "def f(self):\n    return (self.b - self.a).total_seconds()\n")["passthrough"] is False
    assert receipts.classify_match("a.py", "def f(x):\n    return ''.join(x)\n")["passthrough"] is False
    info = receipts.classify_match("a.py", "def f(a):\n    return mod.g(a)\n")
    assert info["name"] == "f" and info["callee"] == "mod.g"


def test_ts_passthrough_detection():
    assert receipts.classify_match("a.ts", "export function f(a: string, b: number) { return g(a, b) }")["passthrough"] is True
    assert receipts.classify_match("a.ts", "const f = (a, b) => g(a, b)")["passthrough"] is True
    assert receipts.classify_match("a.ts", "const f = async (a) => svc.g(a)")["passthrough"] is True
    assert receipts.classify_match("a.ts", "function f(a, b) { return g(b, a) }")["passthrough"] is False
    assert receipts.classify_match("a.ts", "function f(a) { return g(a.id) }")["passthrough"] is False
    assert receipts.classify_match("a.tsx", "function f(a) { return g(a, 1) }")["passthrough"] is False


def test_detect_and_applicable():
    stack = receipts.detect(Path("."), ["src/a.py", "pyproject.toml", "README.md"])
    assert stack["stacks"] == ["py"]
    plan = receipts.applicable(stack["stacks"])
    assert plan["ruff"] is None and plan["knip"] and plan["depcruise"]
    js = receipts.detect(Path("."), ["package.json", "src/index.ts", "node_modules/x/y.js"])
    assert js["stacks"] == ["js"]


def test_code_files_skips_vendored_dirs():
    files = ["src/a.ts", "node_modules/x/b.ts", "dist/c.js", "docs/d.md", ".venv/lib/e.py", "e.py"]
    assert receipts.code_files(files, receipts.JS_EXT | receipts.PY_EXT) == ["src/a.ts", "e.py"]


def test_hotspots_join_churn_with_sizes():
    size = {"largest": [{"file": "a.py", "lines": 100}, {"file": "b.py", "lines": 10}]}
    ch = {"hottest": [{"file": "b.py", "changes": 30}, {"file": "a.py", "changes": 2}, {"file": "c.py", "changes": 1}]}
    top = receipts.hotspots(size, ch)
    assert [t["file"] for t in top] == ["b.py", "a.py", "c.py"]
    assert top[0]["score"] == 300 and top[2]["lines"] is None


def test_sizes_on_this_repo():
    files = receipts.tracked_files(REPO)
    s = receipts.sizes(REPO, files)
    assert s["files"] >= 3 and s["lines"] > 100
    assert s["largest"][0]["lines"] >= s["largest"][-1]["lines"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("OK")
