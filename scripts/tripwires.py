#!/usr/bin/env python3
"""Numeric tripwires over a unified diff. Warn, never block.

Reads a unified diff on stdin and prints JSON: lines added and removed, files added
and deleted, newly exported top-level symbols, and new dependency lines. Each
threshold crossed becomes one warning string. Danger.js shape: the numbers are a
prompt for a sentence of justification, not a gate.

    git diff main...HEAD | python3 tripwires.py [--loc-limit 200] [--text]

Standard library only, 3.9-compatible.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Dict, List, Optional

LOC_LIMIT = 200

# Top-level symbols that leave the file. One pattern per language family; a language
# not listed contributes no export tripwire rather than a wrong one.
EXPORT_PATTERNS = {
    ".py": re.compile(r"^(?:async\s+)?(?:def|class)\s+([A-Za-z]\w*)"),
    ".ts": re.compile(
        r"^export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|var|interface|type|enum)\s+(\w+)"
    ),
    ".go": re.compile(r"^(?:func\s+(?:\([^)]*\)\s*)?|type\s+)([A-Z]\w*)"),
    ".rs": re.compile(r"^pub(?:\([^)]*\))?\s+(?:async\s+)?(?:fn|struct|enum|trait|type|mod|const|static)\s+(\w+)"),
}
EXPORT_ALIASES = {".tsx": ".ts", ".js": ".ts", ".jsx": ".ts", ".mjs": ".ts", ".cjs": ".ts"}

PACKAGE_JSON_TOP_LEVEL = {
    "name", "version", "description", "main", "module", "types", "type", "private",
    "license", "author", "homepage", "repository", "bugs", "keywords", "scripts", "engines",
    "files", "bin", "exports", "packageManager", "workspaces", "browser", "sideEffects",
}
DEP_SECTIONS_TOML = {"dependencies", "dev-dependencies", "build-dependencies"}


def _ext(path: str) -> str:
    dot = path.rfind(".")
    ext = path[dot:] if dot >= 0 else ""
    return EXPORT_ALIASES.get(ext, ext)


def _basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def _export(path: str, line: str) -> Optional[str]:
    pattern = EXPORT_PATTERNS.get(_ext(path))
    if pattern is None:
        return None
    match = pattern.match(line)
    if not match:
        return None
    name = match.group(1)
    if _ext(path) == ".py" and name.startswith("_"):
        return None
    return name


def _dependency(path: str, line: str, section: Optional[str]) -> Optional[str]:
    base = _basename(path)
    stripped = line.strip()
    if base == "package.json":
        match = re.match(r'"([^"]+)"\s*:\s*"[^"]*"', stripped)
        if match and match.group(1) not in PACKAGE_JSON_TOP_LEVEL:
            return match.group(1)
    elif base == "pyproject.toml":
        match = re.match(r'"([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*(?:[<>=~!;].*)?",?$', stripped)
        if match and section and (section == "project" or "dependencies" in section or "dependency-groups" in section):
            return match.group(1)
    elif base == "Cargo.toml":
        match = re.match(r"([A-Za-z0-9_-]+)\s*=", stripped)
        if match and section and section.split(".")[-1] in DEP_SECTIONS_TOML:
            return match.group(1)
    elif base == "go.mod":
        match = re.match(r"([\w./-]+)\s+v\S+", stripped)
        if match and not stripped.startswith(("module", "go ", "toolchain")):
            return match.group(1)
    elif base.startswith("requirements") and base.endswith(".txt"):
        if stripped and not stripped.startswith(("#", "-")):
            return re.split(r"[<>=~!\[; ]", stripped, maxsplit=1)[0]
    return None


def analyze(diff: str, loc_limit: int = LOC_LIMIT) -> Dict[str, object]:
    added = removed = 0
    files_changed: List[str] = []
    files_added: List[str] = []
    files_deleted: List[str] = []
    new_exports: List[Dict[str, object]] = []
    new_deps: List[Dict[str, str]] = []

    path = ""
    old_path = ""
    old_is_null = False
    new_line = 0
    toml_section: Optional[str] = None

    for raw in diff.splitlines():
        if raw.startswith("--- "):
            source = raw[4:].strip()
            old_is_null = source == "/dev/null"
            old_path = source[2:] if source.startswith("a/") else source
            continue
        if raw.startswith("+++ "):
            target = raw[4:].strip()
            if target == "/dev/null":
                path = old_path
                files_deleted.append(path)
                files_changed.append(path)
                continue
            path = target[2:] if target.startswith("b/") else target
            files_changed.append(path)
            if old_is_null:
                files_added.append(path)
            toml_section = None
            continue
        if raw.startswith("@@"):
            match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", raw)
            new_line = int(match.group(1)) if match else 0
            continue
        if not path:
            continue
        if raw.startswith("+"):
            content = raw[1:]
            added += 1
            if _basename(path).endswith(".toml"):
                header = re.match(r"\s*\[+([^\]]+)\]+", content)
                if header:
                    toml_section = header.group(1).strip()
            name = _export(path, content)
            if name:
                new_exports.append({"file": path, "line": new_line, "symbol": name})
            dep = _dependency(path, content, toml_section)
            if dep:
                new_deps.append({"file": path, "name": dep})
            new_line += 1
        elif raw.startswith("-"):
            removed += 1
        elif raw.startswith(" "):
            content = raw[1:]
            if _basename(path).endswith(".toml"):
                header = re.match(r"\s*\[+([^\]]+)\]+", content)
                if header:
                    toml_section = header.group(1).strip()
            new_line += 1

    changed = added + removed
    warnings: List[str] = []
    if changed >= loc_limit:
        warnings.append(f"{changed} lines changed (+{added}/-{removed}); warn at {loc_limit}")
    if files_added:
        warnings.append(f"{len(files_added)} new file(s): {', '.join(files_added)}")
    if new_exports:
        names = ", ".join(f"{e['symbol']} ({e['file']}:{e['line']})" for e in new_exports)
        warnings.append(f"{len(new_exports)} new exported symbol(s): {names}")
    if new_deps:
        names = ", ".join(sorted({d["name"] for d in new_deps}))
        warnings.append(f"{len(new_deps)} new dependency line(s): {names}")

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "loc_limit": loc_limit,
        "files": {
            "changed": len(files_changed),
            "added": files_added,
            "deleted": files_deleted,
        },
        "new_exports": new_exports,
        "new_deps": new_deps,
        "warnings": warnings,
    }


def render(result: Dict[str, object]) -> str:
    files = result["files"]
    head = (
        f"Tripwires: +{result['added']}/-{result['removed']} lines across {files['changed']} file(s)"
        f" · {len(files['added'])} new · {len(result['new_exports'])} new export(s)"
        f" · {len(result['new_deps'])} new dep line(s)"
    )
    warnings = result["warnings"]
    if not warnings:
        return head + " · none crossed"
    return head + "\n" + "\n".join(f"  ! {w}" for w in warnings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--loc-limit", type=int, default=LOC_LIMIT)
    parser.add_argument("--text", action="store_true", help="one-line summary instead of JSON")
    args = parser.parse_args()
    result = analyze(sys.stdin.read(), args.loc_limit)
    print(render(result) if args.text else json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
