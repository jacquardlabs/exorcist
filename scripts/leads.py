#!/usr/bin/env python3
"""Behavior-change leads: where the repo still references a value a diff retires.

Reads a unified diff on stdin and prints JSON. A value is retired when a '-' line
carries it and no '+' line anywhere in the diff carries it the same way: a
`key: value` scalar (YAML, frontmatter) by the same key, a quoted or backticked
literal as the same literal, a code identifier as the same identifier. For each
retired value, every file outside the diff that references it, test files first,
as path:line and the line's text. The lanes read each lead; this script decides
nothing.

    python3 leads.py [--repo ROOT] [--min-len 4] [--per-value 20] [--total 200] < diff.patch

Noise is filtered deterministically and every filter reports a count: tokens shorter
than --min-len, keywords and stopwords, values still on the '+' side, values nothing
outside the diff references. Caps keep test references first; what they drop is
counted per value and in total, never silently. Standard library only,
3.9-compatible; uses `git grep` when ROOT is a git work tree, else walks it.
"""
from __future__ import annotations

import argparse
import json
import keyword
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterator, List, Set, Tuple

MIN_LEN = 4
PER_VALUE = 20
TOTAL = 200
TEXT_WIDTH = 200

PROSE_EXTS = {".md", ".mdx", ".markdown", ".rst", ".txt", ""}
YAML_EXTS = {".yml", ".yaml", ".md", ".mdx", ".markdown"}
COMMENT_PREFIXES = ("#", "//", "/*", "*", "<!--", "--", ";")

STOPWORDS = frozenset(
    {k.lower() for k in keyword.kwlist}
    | {
        # JS/TS, Go, Rust, shell, and literal words Python's keyword list lacks
        "const", "function", "let", "var", "this", "self", "cls", "new", "typeof",
        "instanceof", "void", "undefined", "null", "none", "true", "false", "yes",
        "export", "default", "extends", "implements", "interface", "type", "enum",
        "public", "private", "protected", "static", "readonly", "async", "await",
        "func", "package", "struct", "impl", "trait", "match", "loop", "then", "done",
        "echo", "local", "string", "number", "object", "boolean", "list", "dict",
        "print", "require", "module", "exports", "switch", "case", "throw", "catch",
        # short English that survives the length floor
        "that", "with", "have", "they", "will", "what", "when", "where", "which",
        "there", "their", "been", "were", "into", "than", "them", "some", "only",
        "also", "each", "must", "more", "most", "such", "does", "just", "like", "over",
        "very", "your", "about", "after", "before", "every", "other", "these", "those",
        "would", "could", "should", "still",
    }
)

TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs"}
TEST_NAME = re.compile(r"(?:^|[._-])(?:tests?|spec)(?:[._-]|$)|^test|(?:Tests?|Spec)\.[^.]+$", re.IGNORECASE)

YAML_PAIR = re.compile(r"""^\s*(?:-\s+)?([A-Za-z_][\w.-]*):\s+["']?([^\s"'#]+)["']?\s*(?:#.*)?$""")
LITERAL = re.compile(r'"([^"\\\n]*)"|\'([^\'\\\n]*)\'|`([^`\n]*)`')
BACKTICK = re.compile(r"`([^`\n]+)`")
IDENT = re.compile(r"[A-Za-z_]\w*")
# A bare word on a code line counts only in code position — defined, called, assigned,
# or dotted — or when no English word is shaped like it (snake_case, camelCase, digits).
DEFINER = re.compile(r"\b(?:def|class|function|const|let|var|type|interface|struct|enum|fn|func)\s+$")
CODE_SHAPE = re.compile(r"_|\d|[a-z][A-Z]")
TAIL_CODE = re.compile(r"(?:\(|\.[A-Za-z_]|\[|\s*=(?!=))")

Value = Tuple[str, str, str]  # (kind, key, token); key is "" unless kind is "yaml"


def _ext(path: str) -> str:
    base = path.rsplit("/", 1)[-1]
    dot = base.rfind(".")
    return base[dot:].lower() if dot > 0 else ""


def is_test(path: str) -> bool:
    """A test path that can assert: prose under tests/ documents, it does not pin."""
    parts = path.split("/")
    if _ext(path) in PROSE_EXTS:
        return False
    return any(p.lower() in TEST_DIRS for p in parts[:-1]) or bool(TEST_NAME.search(parts[-1]))


def _as_retired(text: str, token: str, keys: Set[str]) -> bool:
    """The reference carries the value the way the diff retired it: quoted, or under its key."""
    quoted = re.search("[\"'`]" + re.escape(token) + "[\"'`]", text)
    keyed = any(re.search(re.escape(k) + r":\s*[\"']?" + re.escape(token) + r"(?!\w)", text) for k in keys)
    return bool(quoted or keyed)


def _code_idents(line: str) -> Iterator[str]:
    for m in IDENT.finditer(line):
        word = m.group(0)
        before, after = line[: m.start()], line[m.end():]
        if (
            CODE_SHAPE.search(word)
            or before.endswith(".")
            or DEFINER.search(before)
            or TAIL_CODE.match(after)
        ):
            yield word


def values(path: str, line: str) -> Set[Value]:
    """Every typed value one diff line carries."""
    ext = _ext(path)
    found: Set[Value] = set()
    if ext in YAML_EXTS:
        pair = YAML_PAIR.match(line)
        if pair:
            found.add(("yaml", pair.group(1), pair.group(2)))
    stripped = line.strip()
    if ext in PROSE_EXTS or stripped.startswith(COMMENT_PREFIXES):
        found.update(("literal", "", m.group(1).strip()) for m in BACKTICK.finditer(line))
        return found
    found.update(
        ("literal", "", next(g for g in m.groups() if g is not None).strip())
        for m in LITERAL.finditer(line)
    )
    code = LITERAL.sub('""', line)
    code = re.split(r"\s#|\s//|^#|^//", code, maxsplit=1)[0]
    found.update(("ident", "", word) for word in _code_idents(code))
    return found


def parse(diff: str) -> Tuple[Set[str], List[Tuple[str, int, str]], List[Tuple[str, str]]]:
    """Changed paths (both sides), '-' lines as (path, old line, text), '+' lines as (path, text)."""
    changed: Set[str] = set()
    minus: List[Tuple[str, int, str]] = []
    plus: List[Tuple[str, str]] = []
    old_path = new_path = ""
    old_line = old_left = new_left = 0
    for raw in diff.splitlines():
        if old_left > 0 or new_left > 0:
            tag, body = raw[:1], raw[1:]
            if tag == "-":
                minus.append((old_path, old_line, body))
                old_line += 1
                old_left -= 1
            elif tag == "+":
                plus.append((new_path, body))
                new_left -= 1
            elif tag in (" ", ""):
                old_line += 1
                old_left -= 1
                new_left -= 1
            continue
        if raw.startswith("--- "):
            source = raw[4:].strip()
            old_path = source[2:] if source.startswith("a/") else source
        elif raw.startswith("+++ "):
            target = raw[4:].strip()
            new_path = target[2:] if target.startswith("b/") else target
            if new_path == "/dev/null":
                new_path = old_path
            changed.update(p for p in (old_path, new_path) if p != "/dev/null")
            if old_path == "/dev/null":
                old_path = new_path
        elif raw.startswith("@@"):
            m = re.match(r"@@ -(\d+)(?:,(\d+))? \+\d+(?:,(\d+))? @@", raw)
            if m:
                old_line = int(m.group(1))
                old_left = int(m.group(2)) if m.group(2) is not None else 1
                new_left = int(m.group(3)) if m.group(3) is not None else 1
    return changed, minus, plus


def _grep(root: Path, token: str) -> List[Tuple[str, int, str]]:
    word = bool(re.match(r"\w", token) and re.search(r"\w$", token))
    cmd = ["git", "-C", str(root), "grep", "-n", "-I", "-F", "--untracked", "--full-name"]
    try:
        done = subprocess.run(
            [*cmd, *(["-w"] if word else []), "-e", token, "--"],
            capture_output=True, text=True, check=False, errors="replace",
        )
    except FileNotFoundError:
        done = None
    # Exit 1 with nothing on stderr is "no match"; anything else means git could not search.
    if done is not None and (done.returncode == 0 or (done.returncode == 1 and not done.stderr.strip())):
        hits = (line.split(":", 2) for line in done.stdout.splitlines())
        return [(h[0], int(h[1]), h[2]) for h in hits if len(h) == 3 and h[1].isdigit()]
    return _walk(root, token, word)


def _walk(root: Path, token: str, word: bool) -> List[Tuple[str, int, str]]:
    pattern = re.compile((r"(?<!\w)" + re.escape(token) + r"(?!\w)") if word else re.escape(token))
    hits: List[Tuple[str, int, str]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        for name in sorted(filenames):
            full = Path(dirpath) / name
            try:
                data = full.read_bytes()
            except OSError:
                continue
            if b"\0" in data:
                continue
            rel = full.relative_to(root).as_posix()
            lines = data.decode("utf-8", errors="replace").splitlines()
            hits.extend((rel, n, text) for n, text in enumerate(lines, 1) if pattern.search(text))
    return hits


def leads(
    diff: str,
    root: Path,
    min_len: int = MIN_LEN,
    per_value: int = PER_VALUE,
    total: int = TOTAL,
) -> Dict[str, object]:
    changed, minus, plus = parse(diff)
    added = {v for path, text in plus for v in values(path, text)}
    retired: Dict[Value, List[Tuple[str, int, str]]] = {}
    for path, line, text in minus:
        for value in values(path, text):
            retired.setdefault(value, []).append((path, line, text))

    filtered = {"short": 0, "keyword": 0, "still_added": 0, "unreferenced": 0}
    by_token: Dict[str, Dict[str, object]] = {}
    for value in sorted(retired):
        kind, key, token = value
        if len(token) < min_len or not re.search(r"[A-Za-z_]", token):
            filtered["short"] += 1
        elif token.lower() in STOPWORDS:
            filtered["keyword"] += 1
        elif value in added:
            filtered["still_added"] += 1
        else:
            entry = by_token.setdefault(token, {"kinds": set(), "keys": set(), "retired": []})
            entry["kinds"].add(kind)
            entry["keys"].update([key] if key else [])
            entry["retired"].extend(retired[value])

    # Test references first; within them, the ones that carry the value as the diff
    # retired it (quoted, or under its key) before bare-word mentions.
    candidates = []
    for token in sorted(by_token):
        keys = by_token[token]["keys"]
        refs = sorted(
            (h for h in _grep(root, token) if h[0] not in changed),
            key=lambda h: (not is_test(h[0]), not _as_retired(h[2], token, keys), h[0], h[1]),
        )
        if not refs:
            filtered["unreferenced"] += 1
            continue
        candidates.append((token, by_token[token], refs))

    # Per-value cap first, then the total cap spends its budget on test references
    # across every value before any non-test reference.
    kept = {token: refs[:per_value] for token, _, refs in candidates}
    ranked = sorted(
        ((not is_test(h[0]), i, j) for i, (token, _, _) in enumerate(candidates) for j, h in enumerate(kept[token])),
    )
    survivors = {(i, j) for _, i, j in ranked[:total]}

    out = []
    for i, (token, entry, refs) in enumerate(candidates):
        shown = [h for j, h in enumerate(kept[token]) if (i, j) in survivors]
        out.append({
            "value": token,
            "kinds": sorted(entry["kinds"]),
            "retired": [f"{p}:{n}" for p, n, _ in sorted(set(entry["retired"]))],
            "refs": [
                {"path": p, "line": n, "test": is_test(p), "text": t.strip()[:TEXT_WIDTH]}
                for p, n, t in shown
            ],
            "dropped": len(refs) - len(shown),
        })

    ref_count = sum(len(lead["refs"]) for lead in out)
    return {
        "leads": out,
        "totals": {
            "values": len(out),
            "refs": ref_count,
            "test_refs": sum(r["test"] for lead in out for r in lead["refs"]),
            "dropped_per_value": sum(len(refs) - len(kept[token]) for token, _, refs in candidates),
            "dropped_total": len(ranked) - len(survivors),
        },
        "filtered": filtered,
        "caps": {"min_len": min_len, "per_value": per_value, "total": total},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--repo", default=".", help="repository root to search (default: .)")
    parser.add_argument("--min-len", type=int, default=MIN_LEN)
    parser.add_argument("--per-value", type=int, default=PER_VALUE)
    parser.add_argument("--total", type=int, default=TOTAL)
    args = parser.parse_args()
    result = leads(sys.stdin.read(), Path(args.repo), args.min_len, args.per_value, args.total)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
