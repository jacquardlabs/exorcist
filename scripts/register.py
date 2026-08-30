#!/usr/bin/env python3
"""Validate, rank, and render a séance register (reference/register.md).

    python3 register.py validate <register.json>
    python3 register.py rank <register.json>          # rewrites rank in place, sorted
    python3 register.py render <register.json>        # markdown to stdout
    python3 register.py merge <out.json> <lane.json>... --repo R --ref SHA --receipts DIR

Standard library only, 3.9-compatible.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

LANES = ("contention", "dead", "duplicate", "strata")
STATUSES = ("proposed", "approved", "held", "banished", "skipped")
EVIDENCE_KINDS = ("grep", "tool", "trace", "read")
# What lanes actually write, mapped to the vocabulary. Fixed here, at the boundary.
KIND_ALIASES = {"clone": "tool", "receipt": "tool", "surface": "read", "file": "read", "count": "grep", "search": "grep", "callers": "trace"}
SITE_ROLES = ("banish", "migrate", "keep")
CONFIDENCE = ("sourced", "inferred")
ID_RE = re.compile(r"^G-\d{2,}$")
GHOST_REQUIRED = (
    "id", "lane", "title", "status", "concepts", "evidence", "sites",
    "blast_radius", "banishment", "confidence",
)
RADIUS_REQUIRED = ("files", "callers", "exported", "tests")


def validate_ghost(ghost: Dict[str, Any], where: str) -> List[str]:
    errors = [f"{where}: missing {k}" for k in GHOST_REQUIRED if k not in ghost]
    if errors:
        return errors
    if not ID_RE.match(str(ghost["id"])):
        errors.append(f"{where}: id {ghost['id']!r} must look like G-01")
    if ghost["lane"] not in LANES:
        errors.append(f"{where}: lane {ghost['lane']!r} not in {LANES}")
    if ghost["status"] not in STATUSES:
        errors.append(f"{where}: status {ghost['status']!r} not in {STATUSES}")
    if ghost["confidence"] not in CONFIDENCE:
        errors.append(f"{where}: confidence {ghost['confidence']!r} not in {CONFIDENCE}")
    if not isinstance(ghost["concepts"], list) or not ghost["concepts"]:
        errors.append(f"{where}: concepts must be a non-empty list — it is the score")
    if not isinstance(ghost["evidence"], list) or not ghost["evidence"]:
        errors.append(f"{where}: evidence must be a non-empty list")
    else:
        for i, ev in enumerate(ghost["evidence"]):
            if not isinstance(ev, dict) or ev.get("kind") not in EVIDENCE_KINDS or not ev.get("detail"):
                errors.append(f"{where}.evidence[{i}]: needs kind in {EVIDENCE_KINDS} and detail")
    if not isinstance(ghost["sites"], list) or not ghost["sites"]:
        errors.append(f"{where}: sites must be a non-empty list")
    else:
        for i, site in enumerate(ghost["sites"]):
            if not isinstance(site, dict) or not site.get("path") or site.get("role") not in SITE_ROLES:
                errors.append(f"{where}.sites[{i}]: needs path and role in {SITE_ROLES}")
    radius = ghost["blast_radius"]
    if not isinstance(radius, dict):
        errors.append(f"{where}: blast_radius must be an object")
    else:
        errors.extend(f"{where}.blast_radius: missing {k}" for k in RADIUS_REQUIRED if k not in radius)
    if not isinstance(ghost["banishment"], str) or "\n" in ghost["banishment"].strip():
        errors.append(f"{where}: banishment must be one line")
    if ghost["confidence"] == "sourced" and any(
        isinstance(ev, dict) and ev.get("kind") == "trace" and not ev.get("receipt")
        for ev in ghost["evidence"]
    ):
        pass  # a trace is sourced when the lane ran it; nothing to check without the tree
    return errors


def validate(register: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if register.get("exorcist_register") != 1:
        errors.append("exorcist_register must be 1")
    errors += [f"missing {key}" for key in ("repo", "ref", "generated", "ghosts") if key not in register]
    ghosts = register.get("ghosts")
    if not isinstance(ghosts, list):
        errors.append("ghosts must be a list")
        return errors
    seen = set()
    for i, ghost in enumerate(ghosts):
        where = f"ghosts[{i}]"
        if not isinstance(ghost, dict):
            errors.append(f"{where}: not an object")
            continue
        errors.extend(validate_ghost(ghost, where))
        gid = ghost.get("id")
        if gid in seen:
            errors.append(f"{where}: duplicate id {gid}")
        seen.add(gid)
    return errors


def _radius_size(ghost: Dict[str, Any]) -> int:
    radius = ghost.get("blast_radius") or {}
    return int(radius.get("files", 0)) + int(radius.get("callers", 0)) + int(radius.get("tests", 0))


def rank(register: Dict[str, Any]) -> Dict[str, Any]:
    """Concepts desc, sourced before inferred, blast radius asc. Held ghosts keep
    their score — the human should see them where they belong, not at the bottom."""
    ghosts = sorted(
        register["ghosts"],
        key=lambda g: (
            -len(g.get("concepts", [])),
            0 if g.get("confidence") == "sourced" else 1,
            _radius_size(g),
            str(g.get("id")),
        ),
    )
    for i, ghost in enumerate(ghosts, 1):
        ghost["rank"] = i
    register["ghosts"] = ghosts
    return register


def _radius_text(ghost: Dict[str, Any]) -> str:
    r = ghost.get("blast_radius") or {}
    exported = " · exported" if r.get("exported") else ""
    return f"{r.get('files', '?')}f/{r.get('callers', '?')}c/{r.get('tests', '?')}t{exported}"


def render(register: Dict[str, Any]) -> str:
    ghosts = register.get("ghosts", [])
    ref = str(register.get("ref", ""))[:12]
    total = sum(len(g.get("concepts", [])) for g in ghosts)
    lines = [
        f"# Séance — {register.get('repo', '?')} @ {ref} · {register.get('generated', '')}",
        "",
        f"{len(ghosts)} ghost(s) · {total} concept(s) on the table",
    ]
    lanes = register.get("lanes") or {}
    silent = [k for k, v in lanes.items() if v != "reported"]
    if silent:
        lines.append(f"Lanes that did not report: {', '.join(silent)}")
    lines += ["", "| # | id | lane | status | ghost | concepts | radius | banishment |", "|---|---|---|---|---|---|---|---|"]
    for g in ghosts:
        hold = f" ⚠ {g['hold']}" if g.get("hold") else ""
        lines.append(
            f"| {g.get('rank', '')} | {g['id']} | {g['lane']} | {g['status']}{hold} | {g['title']} "
            f"| {len(g.get('concepts', []))} | {_radius_text(g)} | {g['banishment']} |"
        )
    for g in ghosts:
        lines += ["", f"## {g['id']} — {g['title']}", ""]
        lines.append(f"`{g['lane']}` · `{g['status']}` · {g['confidence']}" + (f" · **hold: {g['hold']}**" if g.get("hold") else ""))
        lines.append("")
        lines.append("**Retires.** " + ", ".join(f"`{c}`" for c in g.get("concepts", [])))
        if g.get("survivor"):
            lines.append(f"**Survivor.** `{g['survivor']}`")
        lines.append("")
        lines.append("**Evidence.**")
        for ev in g.get("evidence", []):
            receipt = f" (`{ev['receipt']}`)" if ev.get("receipt") else ""
            lines.append(f"- {ev.get('kind')}: {ev.get('detail')}{receipt}")
        lines.append("")
        lines.append("**Sites.**")
        for s in g.get("sites", []):
            line = f":{s['line']}" if s.get("line") is not None else ""
            lines.append(f"- `{s['path']}{line}` — {s['role']}")
        lines.append("")
        lines.append(f"**Banishment.** {g['banishment']}")
        if g.get("outcome"):
            lines.append("")
            lines.append(f"**Outcome.** {g['outcome']}")
    return "\n".join(lines) + "\n"


def _normalize(ghost: Dict[str, Any]) -> None:
    """Lane replies cross a transport that HTML-escapes text and lanes coin evidence
    kinds; both are fixed here so nothing downstream has to know."""
    for key in ("title", "banishment", "survivor", "hold"):
        if isinstance(ghost.get(key), str):
            ghost[key] = html.unescape(ghost[key])
    ghost["concepts"] = [html.unescape(c) if isinstance(c, str) else c for c in ghost.get("concepts", [])]
    for ev in ghost.get("evidence", []) or []:
        if isinstance(ev, dict):
            ev["kind"] = KIND_ALIASES.get(str(ev.get("kind")), ev.get("kind"))
            if isinstance(ev.get("detail"), str):
                ev["detail"] = html.unescape(ev["detail"])


def merge(lane_files: List[Path], repo: str, ref: str, receipts: str) -> Dict[str, Any]:
    """Combine per-lane replies into one register. A lane file that does not parse as
    a JSON array is recorded as 'did not report' and never repaired."""
    lanes: Dict[str, str] = {}
    ghosts: List[Dict[str, Any]] = []
    for path in lane_files:
        lane = path.stem
        try:
            text = path.read_text(encoding="utf-8").strip()
            fence = re.match(r"^```[a-zA-Z]*\n(.*)\n```$", text, re.S)
            if fence:
                text = fence.group(1)
            data = json.loads(text)
        except (OSError, json.JSONDecodeError):
            lanes[lane] = "did not report"
            continue
        if not isinstance(data, list):
            lanes[lane] = "did not report"
            continue
        lanes[lane] = "reported"
        for ghost in data:
            if isinstance(ghost, dict):
                _normalize(ghost)
                ghost.setdefault("lane", lane)
                ghost.setdefault("status", "proposed")
                ghost.setdefault("hold", None)
                ghost.setdefault("survivor", None)
                ghost.setdefault("outcome", None)
                ghosts.append(ghost)
    for i, ghost in enumerate(ghosts, 1):
        ghost["id"] = f"G-{i:02d}"
    register = {
        "exorcist_register": 1,
        "repo": repo,
        "ref": ref,
        "generated": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "receipts": receipts,
        "lanes": lanes,
        "ghosts": ghosts,
    }
    return rank(register)


def _load(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _save(path: str, register: Dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate").add_argument("path")
    sub.add_parser("rank").add_argument("path")
    sub.add_parser("render").add_argument("path")
    m = sub.add_parser("merge")
    m.add_argument("out")
    m.add_argument("lanes", nargs="+")
    m.add_argument("--repo", required=True)
    m.add_argument("--ref", required=True)
    m.add_argument("--receipts", default="")
    args = parser.parse_args()

    if args.cmd == "merge":
        register = merge([Path(p) for p in args.lanes], args.repo, args.ref, args.receipts)
        errors = validate(register)
        _save(args.out, register)
        silent = [k for k, v in register["lanes"].items() if v != "reported"]
        print(f"{len(register['ghosts'])} ghost(s) → {args.out}" + (f" · did not report: {', '.join(silent)}" if silent else ""))
        if errors:
            print("Register has validation errors (kept as written):")
            for e in errors:
                print(f"  - {e}")
            return 1
        return 0

    register = _load(args.path)
    if args.cmd == "validate":
        errors = validate(register)
        if errors:
            print("Register invalid:")
            for e in errors:
                print(f"  - {e}")
            return 1
        print(f"Register valid: {len(register['ghosts'])} ghost(s).")
        return 0
    if args.cmd == "rank":
        _save(args.path, rank(register))
        print(f"Ranked {len(register['ghosts'])} ghost(s).")
        return 0
    if args.cmd == "render":
        sys.stdout.write(render(register))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
