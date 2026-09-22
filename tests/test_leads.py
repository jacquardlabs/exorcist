#!/usr/bin/env python3
"""Unit tests for scripts/leads.py. Self-running: prints OK."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import leads  # noqa: E402


def _tree(tmp, files, git=True):
    for rel, text in files.items():
        path = Path(tmp) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    if git:
        for args in (["init", "-q"], ["add", "-A"]):
            subprocess.run(["git", "-C", tmp, *args], check=True, capture_output=True)
    return Path(tmp)


def _refs(result, value):
    lead = next(lead for lead in result["leads"] if lead["value"] == value)
    return [f"{r['path']}:{r['line']}" for r in lead["refs"]], lead


FRONTMATTER_DIFF = """\
diff --git a/agents/auditor.md b/agents/auditor.md
--- a/agents/auditor.md
+++ b/agents/auditor.md
@@ -1,4 +1,4 @@
 ---
 name: auditor
-model: inherit
+model: claude-opus-5
 ---
diff --git a/CONTRIBUTING.md b/CONTRIBUTING.md
--- a/CONTRIBUTING.md
+++ b/CONTRIBUTING.md
@@ -1,1 +1,1 @@
-Four agents sit at `opus`.
+Never `inherit`: pin a tier.
"""

FRONTMATTER_FILES = {
    "agents/auditor.md": "---\nname: auditor\nmodel: claude-opus-5\n---\n",
    "CONTRIBUTING.md": "Never `inherit`: pin a tier.\n",
    "tests/test_pins.sh": "#!/bin/sh\ncheck \"model recorded verbatim\" \"inherit\" \"$model\"\n",
    "tests/test_other.py": "# children inherit settings from the parent\n",
    "tests/README.md": "Agents that inherit the session model.\n",
    "docs/notes.md": "The `inherit` tier is gone.\n",
}


def test_retired_frontmatter_value_leads_to_the_out_of_diff_test_that_asserts_it():
    with tempfile.TemporaryDirectory() as tmp:
        result = leads.leads(FRONTMATTER_DIFF, _tree(tmp, FRONTMATTER_FILES))
    refs, lead = _refs(result, "inherit")
    # A backticked `inherit` added in prose does not cancel the retired `model: inherit`.
    assert lead["kinds"] == ["yaml"] and lead["retired"] == ["agents/auditor.md:3"], lead
    # Tests first; the one carrying the value quoted before the bare mention; prose under
    # tests/ is not a test; files in the diff never appear.
    assert refs == ["tests/test_pins.sh:2", "tests/test_other.py:1", "docs/notes.md:1", "tests/README.md:1"], refs
    assert [r["test"] for r in lead["refs"]] == [True, True, False, False]
    assert lead["refs"][0]["text"].startswith('check "model recorded verbatim"')
    # `opus` sat in backticks on a '-' line and is retired too, but nothing outside
    # the diff references it.
    assert result["filtered"]["unreferenced"] == 1, result["filtered"]


RENAME_DIFF = """\
diff --git a/src/lib.py b/src/lib.py
--- a/src/lib.py
+++ b/src/lib.py
@@ -1,2 +1,2 @@
-def old_helper(x):
+def new_helper(x):
     return x
"""

RENAME_FILES = {
    "src/lib.py": "def new_helper(x):\n    return x\n",
    "src/app.py": "from lib import old_helper\n\nprint(old_helper(1))\n",
    "tests/test_lib.py": "from lib import old_helper\n\nassert old_helper(2) == 2\n",
    "src/unrelated.py": "old_helper_count = 0\n",
}


def test_renamed_identifier_yields_its_stale_references():
    with tempfile.TemporaryDirectory() as tmp:
        result = leads.leads(RENAME_DIFF, _tree(tmp, RENAME_FILES))
    refs, lead = _refs(result, "old_helper")
    assert lead["kinds"] == ["ident"] and lead["retired"] == ["src/lib.py:1"], lead
    # Whole-word: `old_helper_count` is a different name.
    assert refs == ["tests/test_lib.py:1", "tests/test_lib.py:3", "src/app.py:1", "src/app.py:3"], refs
    assert [lead["value"] for lead in result["leads"]] == ["old_helper"], result["leads"]


NOISE_DIFF = """\
diff --git a/src/queue.py b/src/queue.py
--- a/src/queue.py
+++ b/src/queue.py
@@ -1,3 +1,3 @@
 def drain(self):
-    for item in self.pending_items:
-        return compute_total(item)
+    for item in self.backlog:
+        return compute_total(item, 0)
diff --git a/tests/test_queue.py b/tests/test_queue.py
--- a/tests/test_queue.py
+++ b/tests/test_queue.py
@@ -1,1 +1,1 @@
-assert q.pending_items == []
+assert q.backlog == []
"""

NOISE_FILES = {
    "src/queue.py": "def drain(self):\n    for item in self.backlog:\n        return compute_total(item, 0)\n",
    "tests/test_queue.py": "assert q.backlog == []\n# pending_items used to be here\n",
    "src/other.py": "total = compute_total(self.pending_items)\n",
}


def test_still_added_tokens_keywords_and_diff_plus_lines_are_excluded():
    with tempfile.TemporaryDirectory() as tmp:
        result = leads.leads(NOISE_DIFF, _tree(tmp, NOISE_FILES))
    # compute_total is still on the '+' side; `self` is a keyword; `for`/`in`/`if` are
    # short. tests/test_queue.py is in the diff, but only its '+' line is excluded: the
    # untouched line 2 still references the retired value, test first.
    assert [lead["value"] for lead in result["leads"]] == ["pending_items"], result["leads"]
    refs, _ = _refs(result, "pending_items")
    assert refs == ["tests/test_queue.py:2", "src/other.py:1"], refs
    assert result["filtered"]["still_added"] >= 1 and result["filtered"]["keyword"] >= 1, result["filtered"]


CAP_DIFF = """\
--- a/src/flags.py
+++ b/src/flags.py
@@ -1,2 +1,1 @@
-MODE = "legacy_mode"
-other = alpha_flag(1)
+MODE = "current"
"""

CAP_FILES = {
    **{f"tests/test_a{n}.py": 'assert MODE == "legacy_mode"\n' for n in range(3)},
    **{f"src/m{n}.py": 'x = "legacy_mode"\n' for n in range(3)},
    **{f"tests/test_b{n}.py": "alpha_flag(2)\n" for n in range(2)},
}


def test_caps_keep_tests_first_and_report_dropped_counts():
    with tempfile.TemporaryDirectory() as tmp:
        # No git: the walk fallback searches the same tree.
        result = leads.leads(CAP_DIFF, _tree(tmp, CAP_FILES, git=False), per_value=4, total=5)
    legacy, a = _refs(result, "legacy_mode")
    alpha, b = _refs(result, "alpha_flag")
    # Per-value cap keeps 3 tests + 1 other of 6; the total cap then spends its 5 on the
    # five test references and drops the one non-test survivor.
    assert legacy == [f"tests/test_a{n}.py:1" for n in range(3)], legacy
    assert alpha == ["tests/test_b0.py:1", "tests/test_b1.py:1"], alpha
    assert a["dropped"] == 3 and b["dropped"] == 0, (a, b)
    totals = result["totals"]
    assert totals["refs"] == 5 and totals["dropped_per_value"] == 2 and totals["dropped_total"] == 1, totals


def test_a_git_that_errors_falls_back_to_the_walk():
    def broken(cmd, **_kw):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="xcrun: error")

    real, leads.subprocess.run = leads.subprocess.run, broken
    try:
        with tempfile.TemporaryDirectory() as tmp:
            result = leads.leads(RENAME_DIFF, _tree(tmp, RENAME_FILES, git=False))
    finally:
        leads.subprocess.run = real
    refs, _ = _refs(result, "old_helper")
    assert refs[0] == "tests/test_lib.py:1" and len(refs) == 4, refs


def test_parse_numbers_plus_lines_on_the_new_side():
    diff = "--- a/f.py\n+++ b/f.py\n@@ -3,2 +10,3 @@\n ctx\n-gone\n+one\n+two\n"
    _, minus, plus = leads.parse(diff)
    assert minus == [("f.py", 4, "gone")] and plus == [("f.py", 11, "one"), ("f.py", 12, "two")], (minus, plus)


def test_is_test_paths():
    for path in ("tests/run", "src/FooTest.java", "src/foo.spec.ts", "test_x.py", "pkg/__tests__/a.js"):
        assert leads.is_test(path), path
    for path in ("src/latest.py", "scripts/contest.js", "src/respec.ts", "tests/README.md", "Makefile"):
        assert not leads.is_test(path), path


def test_numeric_tokens_are_counted_apart_from_short_ones():
    diff = "--- a/c.py\n+++ b/c.py\n@@ -1,1 +1,1 @@\n-LIMIT = \"123456\"\n+LIMIT = \"5\"\n"
    with tempfile.TemporaryDirectory() as tmp:
        result = leads.leads(diff, _tree(tmp, {"c.py": 'LIMIT = "5"\n'}))
    assert result["filtered"]["no_letter"] == 1 and result["filtered"]["short"] == 0, result["filtered"]


def test_hunk_counts_keep_a_removed_double_dash_line_out_of_the_headers():
    diff = "--- a/q.sql\n+++ b/q.sql\n@@ -1,2 +1,1 @@\n--- old_table_name note\n select 1;\n"
    changed, minus, plus = leads.parse(diff)
    assert changed == {"q.sql"} and minus == [("q.sql", 1, "-- old_table_name note")] and plus == [], minus


def test_cli_prints_json():
    with tempfile.TemporaryDirectory() as tmp:
        _tree(tmp, RENAME_FILES)
        done = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "leads.py"), "--repo", tmp],
            input=RENAME_DIFF, capture_output=True, text=True, check=True,
        )
    assert json.loads(done.stdout)["totals"]["values"] == 1, done.stdout


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("OK")
