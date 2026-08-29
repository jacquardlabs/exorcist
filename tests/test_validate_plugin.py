#!/usr/bin/env python3
"""Unit tests for scripts/validate_plugin.py. Self-running: prints OK."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import validate_plugin  # noqa: E402 — sys.path must be set first


def _manifest():
    return {
        "name": "exorcist",
        "description": "Aggressive simplification for LLM-generated code.",
        "version": "0.1.0",
        "author": {"name": "Jacquard Labs"},
        "repository": "https://github.com/jacquardlabs/exorcist",
        "license": "MIT",
        "keywords": ["simplification"],
    }


def _has(errors, fragment):
    assert any(fragment in e for e in errors), f"expected {fragment!r} in {errors}"


def test_the_real_manifest_is_valid():
    data = json.loads((REPO / ".claude-plugin/plugin.json").read_text())
    assert validate_plugin.validate(data) == []


def test_every_required_field_is_reported_when_missing():
    for key in validate_plugin.REQUIRED:
        data = _manifest()
        del data[key]
        _has(validate_plugin.validate(data), f"missing required field: {key}")


def test_bad_version_and_name_are_rejected():
    data = _manifest()
    data["version"] = "1.0"
    _has(validate_plugin.validate(data), "not semver")
    data = _manifest()
    data["name"] = "Exorcist!"
    _has(validate_plugin.validate(data), "must match")


def test_author_needs_a_name():
    data = _manifest()
    data["author"] = {}
    _has(validate_plugin.validate(data), "author.name")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("OK")
