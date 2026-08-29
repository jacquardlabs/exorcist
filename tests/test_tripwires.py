#!/usr/bin/env python3
"""Unit tests for scripts/tripwires.py. Self-running: prints OK."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import tripwires  # noqa: E402

PY_DIFF = """\
diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,3 +1,8 @@
 import os
+
+def public_helper(x):
+    return x
+
+def _private(x):
+    return x
-old = 1
diff --git a/src/new_module.py b/src/new_module.py
new file mode 100644
--- /dev/null
+++ b/src/new_module.py
@@ -0,0 +1,2 @@
+class Thing:
+    pass
diff --git a/src/gone.py b/src/gone.py
deleted file mode 100644
--- a/src/gone.py
+++ /dev/null
@@ -1,1 +0,0 @@
-x = 1
"""

TS_DIFF = """\
--- a/src/lib.ts
+++ b/src/lib.ts
@@ -10,2 +10,4 @@
 const a = 1;
+export function retry() {}
+function internal() {}
+export const LIMIT = 3;
"""

DEPS_DIFF = """\
--- a/package.json
+++ b/package.json
@@ -1,5 +1,6 @@
 {
   "name": "x",
+  "version": "1.0.0",
   "dependencies": {
+    "left-pad": "^1.0.0"
   }
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -1,4 +1,6 @@
 [project]
 dependencies = [
+  "httpx>=0.27",
+  "pydantic",
 ]
+[tool.ruff]
+line-length = 100
--- a/Cargo.toml
+++ b/Cargo.toml
@@ -1,3 +1,5 @@
 [package]
+edition = "2021"
 [dependencies]
+serde = "1"
--- a/requirements.txt
+++ b/requirements.txt
@@ -1,1 +1,3 @@
 flask
+# comment
+tenacity==8.0
"""


def test_line_and_file_counts():
    r = tripwires.analyze(PY_DIFF)
    assert r["added"] == 8 and r["removed"] == 2, (r["added"], r["removed"])
    assert r["files"]["added"] == ["src/new_module.py"]
    assert r["files"]["deleted"] == ["src/gone.py"]
    assert r["files"]["changed"] == 3


def test_python_exports_skip_private_and_carry_line_numbers():
    r = tripwires.analyze(PY_DIFF)
    exports = {(e["file"], e["symbol"], e["line"]) for e in r["new_exports"]}
    assert exports == {("src/app.py", "public_helper", 3), ("src/new_module.py", "Thing", 1)}, exports


def test_ts_exports_only_exported_symbols():
    r = tripwires.analyze(TS_DIFF)
    assert [e["symbol"] for e in r["new_exports"]] == ["retry", "LIMIT"]


def test_dependency_lines_by_manifest():
    r = tripwires.analyze(DEPS_DIFF)
    names = sorted(d["name"] for d in r["new_deps"])
    assert names == ["httpx", "left-pad", "pydantic", "serde", "tenacity"], names


def test_warnings_fire_only_when_crossed():
    small = tripwires.analyze(TS_DIFF)
    assert len(small["warnings"]) == 1 and "new exported" in small["warnings"][0]
    big = tripwires.analyze("--- a/x.txt\n+++ b/x.txt\n@@ -1 +1 @@\n" + "+a\n" * 250)
    assert any("250 lines changed" in w for w in big["warnings"])
    clean = tripwires.analyze("--- a/x.txt\n+++ b/x.txt\n@@ -1 +1 @@\n-a\n+b\n")
    assert clean["warnings"] == [] and "none crossed" in tripwires.render(clean)


def test_loc_limit_is_configurable():
    r = tripwires.analyze("--- a/x.txt\n+++ b/x.txt\n@@ -1 +1 @@\n" + "+a\n" * 20, loc_limit=10)
    assert any("warn at 10" in w for w in r["warnings"])


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("OK")
