#!/usr/bin/env python3
"""Behavior-change leads: where the repo still references a value a diff retires.

Reads a unified diff on stdin and prints JSON. A value is retired when a '-' line
carries it and no '+' line anywhere in the diff carries it the same way: a
`key: value` scalar (YAML, or a markdown file's frontmatter) by the same key, a quoted
or backticked literal as the same literal, a code identifier as the same identifier, a
number bound to a name (`MAX_RETRIES = 3`, `retries: 3`) as the same name and number. In
code a bare name must be shaped like code or a constant, so `timeout=30` or `margin: 0`
binds nothing; a quoted key or a YAML key needs no shape, and a test file's code binds
none, since its bindings are fixtures. For each retired value, every line outside the
diff's '+' lines that references it, test files first, as path:line and the line's
text; a bound number's references carry the name and the number together, or, in a
test, the number within PAIR_SPAN lines of the name. The lanes read each lead; this
script decides nothing.

    python3 leads.py [--repo ROOT] [--min-len 4] [--per-value 20] [--total 200] < diff.patch

Noise is filtered deterministically and every filter reports a count: tokens shorter
than --min-len, tokens with no letter (a number bound to a name is judged by the name),
keywords and stopwords, values still on the '+' side, values nothing outside the diff
references. Caps keep test references first; what they drop is
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
from itertools import count, takewhile
from pathlib import Path
from typing import Dict, Iterator, List, Set, Tuple

MIN_LEN = 4
PER_VALUE = 20
TOTAL = 200
TEXT_WIDTH = 200
PAIR_SPAN = 2

PROSE_EXTS = {".md", ".mdx", ".markdown", ".rst", ".txt"}
YAML_EXTS = {".yml", ".yaml"}
FRONTMATTER_EXTS = {".md", ".mdx", ".markdown"}  # YAML only in the leading '---' block
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
TEST_NAME = re.compile(r"(?:^|[._-])(?:tests?|spec)(?:[._-]|$)|^test", re.IGNORECASE)
TEST_CAMEL = re.compile(r"[a-z0-9](?:Tests?|Spec)\.[^.]+$")  # FooTest.java, not latest.py

YAML_PAIR = re.compile(r"""^\s*(?:-\s+)?([A-Za-z_][\w.-]*):\s+["']?([^\s"'#]+)["']?\s*(?:#.*)?$""")
LITERAL = re.compile(r'"([^"\\\n]*)"|\'([^\'\\\n]*)\'|`([^`\n]*)`')
BACKTICK = re.compile(r"`([^`\n]+)`")
IDENT = re.compile(r"[A-Za-z_]\w*")
# A bare word on a code line counts only in code position — defined, called, assigned,
# or dotted — or when no English word is shaped like it (snake_case, camelCase, digits).
DEFINER = re.compile(r"\b(?:def|class|function|const|let|var|type|interface|struct|enum|fn|func)\s+$")
CODE_SHAPE = re.compile(r"_|\d|[a-z][A-Z]")
TAIL_CODE = re.compile(r"(?:\(|\.[A-Za-z_]|\[|\s*=(?!=))")
# A number bound to a name: `NAME = 3`, `const NAME: number = 3`, `name=3)`, `"key": 3,`.
# The number must end the value, so `x = 3 * y`, `x == 3`, and `v: 1.2.3` bind nothing;
# a shell line binds each of `a=0 b=1`.
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
NUM_BIND = re.compile(
    r"""(?<![\w$-])(["']?)([A-Za-z_](?:[\w-]*\w)?)\1(?:\s*:\s*[A-Za-z_][\w.\[\]]*)?"""
    r"""\s*(?::=?|=(?![=>]))\s*(-?\d+(?:\.\d+)?)(?=\s*(?:[,;)}\]]|$)|\s+[A-Za-z_]\w*=(?!=))"""
)

Value = Tuple[str, str, str]  # (kind, key, token); key is "" unless kind is "yaml" or "number"


def _ext(path: str) -> str:
    base = path.rsplit("/", 1)[-1]
    dot = base.rfind(".")
    return base[dot:].lower() if dot > 0 else ""


def is_test(path: str) -> bool:
    """A test path that can assert: prose under tests/ documents, it does not pin."""
    parts = path.split("/")
    if _ext(path) in PROSE_EXTS:
        return False
    return any(p.lower() in TEST_DIRS for p in parts[:-1]) or bool(TEST_NAME.search(parts[-1]) or TEST_CAMEL.search(parts[-1]))


def _as_retired(text: str, token: str, keys: Set[str], name: str = "") -> bool:
    """The reference carries the value the way the diff retired it: quoted, under its
    key, or, for a bound number, beside its name."""
    if name:
        return bool(re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", text))
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


def _slice_or_ternary(line: str, m: "re.Match[str]") -> bool:
    """`xs[start_idx:3]` and `ok ? val : 3` bind nothing: a bare ':' after `[` or `?`."""
    before = line[: m.start()]
    return "=" not in line[m.end(2): m.start(3)] and (before.rstrip().endswith(("[", ":")) or "?" in before)


def values(path: str, line: str, frontmatter: bool = False) -> Set[Value]:
    """Every typed value one diff line carries. A markdown line reads as YAML only when
    it lies in the file's frontmatter."""
    ext = _ext(path)
    found: Set[Value] = set()
    if ext in YAML_EXTS or frontmatter:
        pair = YAML_PAIR.match(line)
        if pair:
            kind = "number" if NUMBER.fullmatch(pair.group(2)) else "yaml"
            found.add((kind, pair.group(1), pair.group(2)))
    stripped = line.strip()
    if ext in PROSE_EXTS or stripped.startswith(COMMENT_PREFIXES):
        found.update(("literal", "", m.group(1).strip()) for m in BACKTICK.finditer(line))
        return found
    found.update(
        ("literal", "", next(g for g in m.groups() if g is not None).strip())
        for m in LITERAL.finditer(line)
    )
    uncommented = re.split(r"\s#|\s//|^#|^//", line, maxsplit=1)[0]
    found.update(
        ("number", m.group(2), m.group(3))
        for m in ([] if is_test(path) else NUM_BIND.finditer(uncommented))
        if (m.group(1) or CODE_SHAPE.search(m.group(2)) or m.group(2).isupper())
        and not _slice_or_ternary(uncommented, m)
    )
    code = LITERAL.sub('""', line)
    code = re.split(r"\s#|\s//|^#|^//", code, maxsplit=1)[0]
    found.update(("ident", "", word) for word in _code_idents(code))
    return found


def _frontmatter_end(lines: List[str]) -> int:
    """The line that closes a '---' block opened at line 1, or 0 when there is none."""
    if not lines or lines[0].strip() != "---":
        return 0
    return next((n for n, text in enumerate(lines[1:], 2) if text.strip() == "---"), 0)


def frontmatter(
    root: Path, paths: Dict[str, str], minus: List[Tuple[str, int, str]], plus: List[Tuple[str, int, str]]
) -> Dict[Tuple[str, str], int]:
    """Where each touched markdown file's frontmatter closes, per side: ('-', old path)
    for the old file, ('+', new path) for the new; PATHS pairs them, so a renamed file's
    old side is rebuilt from its new one. Hunks rarely reach line 1, so the new file is
    read from ROOT and the old one rebuilt from it: the new file without the diff's '+'
    lines, its '-' lines put back at their old numbers. A new file that disagrees with
    the '+' lines is not the diff's new side; each side then knows only the diff lines
    it holds from line 1 on."""
    ends: Dict[Tuple[str, str], int] = {}
    for was, path in sorted(p for p in paths.items() if {_ext(p[0]), _ext(p[1])} & FRONTMATTER_EXTS):
        gone = {n: t for p, n, t in minus if p == was}
        came = {n: t for p, n, t in plus if p == path}
        try:
            new = (root / path).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            new = []
        if not all(n <= len(new) and new[n - 1] == t for n, t in came.items()):
            new = list(takewhile(lambda t: t is not None, (came.get(n) for n in count(1))))
            kept: Iterator[str] = iter(())
        else:
            kept = (t for n, t in enumerate(new, 1) if n not in came)
        sides = (gone[n] if n in gone else next(kept, None) for n in count(1))
        old = list(takewhile(lambda t: t is not None, sides))
        ends[("-", was)], ends[("+", path)] = _frontmatter_end(old), _frontmatter_end(new)
    return ends


def parse(diff: str) -> Tuple[Dict[str, str], List[Tuple[str, int, str]], List[Tuple[str, int, str]]]:
    """Each changed file's old path to its new one, '-' lines as (path, old line, text),
    '+' lines as (path, new line, text). An added or deleted file pairs with itself."""
    paths: Dict[str, str] = {}
    minus: List[Tuple[str, int, str]] = []
    plus: List[Tuple[str, int, str]] = []
    old_path = new_path = ""
    old_line = new_line = old_left = new_left = 0
    for raw in diff.splitlines():
        if old_left > 0 or new_left > 0:
            tag, body = raw[:1], raw[1:]
            if tag == "-":
                minus.append((old_path, old_line, body))
                old_line += 1
                old_left -= 1
            elif tag == "+":
                plus.append((new_path, new_line, body))
                new_line += 1
                new_left -= 1
            elif tag in (" ", ""):
                old_line += 1
                new_line += 1
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
            if old_path == "/dev/null":
                old_path = new_path
            paths[old_path] = new_path
        elif raw.startswith("@@"):
            m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", raw)
            if m:
                old_line, new_line = int(m.group(1)), int(m.group(3))
                old_left = int(m.group(2)) if m.group(2) is not None else 1
                new_left = int(m.group(4)) if m.group(4) is not None else 1
    return paths, minus, plus


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


def _pair_refs(root: Path, name: str, number: str) -> List[Tuple[str, int, str]]:
    """Lines that carry the name and the number together, then test lines that carry
    the bare number within PAIR_SPAN lines of the name. It greps the name and filters
    for the number, not the reverse: a name is rare where a digit is everywhere, so the
    search returns a handful of lines instead of every 3 in the repo."""
    bare = re.compile(r"(?<![\w.-])" + re.escape(number) + r"(?!\w|\.\d)")
    named = _grep(root, name)
    near: List[Tuple[str, int, str]] = []
    for path in sorted({p for p, _, _ in named if is_test(p)}):
        at = {n for p, n, _ in named if p == path}
        try:
            lines = (root / path).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        near.extend(
            (path, n, text) for n, text in enumerate(lines, 1)
            if n not in at and bare.search(text) and any(abs(n - m) <= PAIR_SPAN for m in at)
        )
    return [h for h in named if bare.search(h[2])] + near


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
    paths, minus, plus = parse(diff)
    ends = frontmatter(root, paths, minus, plus)
    added = {v for path, line, text in plus for v in values(path, text, 1 < line < ends.get(("+", path), 0))}
    # A file the diff touches still gets searched: its untouched lines can pin a value
    # the diff retired. Only the diff's own '+' lines are excluded.
    added_at = {(path, line) for path, line, _ in plus}
    retired: Dict[Value, List[Tuple[str, int, str]]] = {}
    for path, line, text in minus:
        for value in values(path, text, 1 < line < ends.get(("-", path), 0)):
            retired.setdefault(value, []).append((path, line, text))

    filtered = {"short": 0, "no_letter": 0, "keyword": 0, "still_added": 0, "unreferenced": 0}
    by_token: Dict[str, Dict[str, object]] = {}
    for value in sorted(retired):
        kind, key, token = value
        # A bound number is judged by its name: the digits alone are never a lead.
        word = key if kind == "number" else token
        if len(word) < min_len:
            filtered["short"] += 1
        elif not re.search(r"[A-Za-z_]", word):
            filtered["no_letter"] += 1
        elif word.lower() in STOPWORDS:
            filtered["keyword"] += 1
        elif value in added:
            filtered["still_added"] += 1
        else:
            shown = f"{key} = {token}" if kind == "number" else token
            entry = by_token.setdefault(shown, {"kinds": set(), "keys": set(), "retired": [], "pair": None})
            entry["kinds"].add(kind)
            if kind == "number":
                entry["pair"] = (key, token)
            else:
                entry["keys"].update([key] if key else [])
            entry["retired"].extend(retired[value])

    # Test references first; within them, the ones that carry the value as the diff
    # retired it (quoted, or under its key) before bare-word mentions.
    candidates = []
    for token in sorted(by_token):
        keys, pair = by_token[token]["keys"], by_token[token]["pair"]
        name = pair[0] if pair else ""
        refs = sorted(
            (h for h in (_pair_refs(root, *pair) if pair else _grep(root, token)) if (h[0], h[1]) not in added_at),
            key=lambda h: (not is_test(h[0]), not _as_retired(h[2], token, keys, name), h[0], h[1]),
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
