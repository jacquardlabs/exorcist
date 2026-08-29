#!/usr/bin/env python3
"""Unit tests for scripts/register.py. Self-running: prints OK."""
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import register  # noqa: E402


def _ghost(**over):
    g = {
        "id": "G-01",
        "lane": "contention",
        "title": "two ways to read a TOML file",
        "status": "proposed",
        "concepts": ["a", "b"],
        "survivor": "src/x.py:1 a",
        "evidence": [{"kind": "grep", "detail": "a: 4 · b: 2", "receipt": None}],
        "sites": [{"path": "src/y.py", "line": 3, "role": "banish"}],
        "blast_radius": {"files": 2, "callers": 2, "exported": False, "tests": 1},
        "banishment": "delete b; point callers at a",
        "confidence": "sourced",
        "hold": None,
        "outcome": None,
    }
    g.update(over)
    return g


def _register(*ghosts):
    return {"exorcist_register": 1, "repo": "o/r", "ref": "abc", "generated": "now", "ghosts": list(ghosts)}


def test_valid_register_passes():
    assert register.validate(_register(_ghost())) == []


def test_missing_evidence_and_concepts_fail():
    errors = register.validate(_register(_ghost(evidence=[]), _ghost(id="G-02", concepts=[])))
    assert any("evidence" in e for e in errors) and any("concepts" in e for e in errors), errors


def test_bad_enums_and_duplicate_ids_fail():
    errors = register.validate(_register(_ghost(lane="spooky"), _ghost(status="done")))
    assert any("lane" in e for e in errors)
    assert any("status" in e for e in errors)
    assert any("duplicate id" in e for e in errors)


def test_rank_orders_by_concepts_then_confidence_then_radius():
    r = _register(
        _ghost(id="G-01", concepts=["a"], blast_radius={"files": 9, "callers": 9, "exported": False, "tests": 0}),
        _ghost(id="G-02", concepts=["a", "b", "c"], confidence="inferred"),
        _ghost(id="G-03", concepts=["a", "b", "c"]),
        _ghost(id="G-04", concepts=["a"]),
    )
    ranked = register.rank(r)
    assert [g["id"] for g in ranked["ghosts"]] == ["G-03", "G-02", "G-04", "G-01"]
    assert [g["rank"] for g in ranked["ghosts"]] == [1, 2, 3, 4]


def test_render_has_table_and_blocks():
    out = register.render(register.rank(_register(_ghost(hold="public API"))))
    assert "| 1 | G-01 | contention | proposed ⚠ public API |" in out
    assert "## G-01 — two ways to read a TOML file" in out
    assert "**Survivor.** `src/x.py:1 a`" in out


def test_merge_normalizes_kinds_and_unescapes_html():
    g = _ghost(title="a -&gt; b", evidence=[{"kind": "clone", "detail": "x &lt; y"}, {"kind": "surface", "detail": "z"}, {"kind": "grep", "detail": "n"}])
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "duplicate.json"
        f.write_text(json.dumps([g]))
        merged = register.merge([f], "o/r", "abc", "")
    ghost = merged["ghosts"][0]
    assert ghost["title"] == "a -> b"
    assert [e["kind"] for e in ghost["evidence"]] == ["tool", "read", "grep"]
    assert ghost["evidence"][0]["detail"] == "x < y"
    assert register.validate(merged) == []


def test_merge_records_silent_lanes_and_unwraps_one_fence():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "contention.json").write_text("```json\n" + json.dumps([_ghost()]) + "\n```")
        (d / "dead.json").write_text("Here are my findings: []")
        (d / "strata.json").write_text("[]")
        merged = register.merge([d / "contention.json", d / "dead.json", d / "strata.json"], "o/r", "abc", "rcpt/")
    assert merged["lanes"] == {"contention": "reported", "dead": "did not report", "strata": "reported"}
    assert [g["id"] for g in merged["ghosts"]] == ["G-01"]
    assert merged["ghosts"][0]["rank"] == 1
    assert register.validate(merged) == []


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("OK")
