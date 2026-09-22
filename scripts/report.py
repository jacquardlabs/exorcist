#!/usr/bin/env python3
"""Resolve the diff base, validate lane findings, merge them into a report draft, and
validate the exorcise report (reference/report.md).

    python3 report.py resolve-base [--base REF] [--pr-base SHA]   # JSON to stdout
    python3 report.py findings <lane.json>
    python3 report.py merge <draft.json> <lane.json>... --tripwires T --scope S [--single-pass]
    python3 report.py validate <report.json>

Exit 0 valid or resolved, 1 invalid, 2 base resolution failed. Standard library
only, 3.9-compatible.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CONTRACT_VERSION = 1
LANES = ("trace", "abstraction", "threshold", "deletion")
ACTIONS = ("revert", "inline", "reuse", "move", "delete", "hold")
TARGETLESS = ("revert", "delete", "hold")
# reference/ghost.md governs; tests/test_report.py fails when this drifts from it.
HOLDS = ("public API", "trust boundary", "behavior change", "spec conflict", "implied by intent", "unmet claim")
# A hold that names a claim no hunk reaches: nothing in the diff to point at.
UNMET = "unmet claim"
CLAIMED = ("implied by intent", UNMET)
# reference/findings.md, highest first: the survivor when two findings claim the same lines.
PRECEDENCE = ("hold", "revert", "delete", "inline", "reuse", "move")
# out_of_intent_files counts a file that carries a trace verdict nothing in the intent reaches.
OUT_OF_INTENT_HOLDS = ("trust boundary",)
BLAST_RADIUS = re.compile(r"^blast radius: \d+ consumers outside the diff$")
FINDING_REQUIRED = ("lane", "file", "line", "end_line", "title", "evidence", "action", "target", "concepts", "hold")
LANE_STATUSES = ("reported", "did not report")
APPLY_STATUSES = ("applied", "skipped")
BASE_SOURCES = ("flag", "pr", "upstream", "main", "head~1")
INTENT_SOURCES = ("text", "pr", "branch")
CHECK_OUTCOMES = ("pass", "fail")
REPORT_REQUIRED = (
    "contract_version", "generated", "branch", "intent", "claims", "scope", "lanes",
    "single_pass", "concepts_removed", "concepts_kept", "applied", "held", "out_of_intent_files",
    "checks", "tripwires", "justifications",
)
SCOPE_REQUIRED = ("base_ref", "base_sha", "head_sha", "source", "includes_worktree", "hunks")
TRIPWIRES_REQUIRED = ("added", "removed", "changed", "loc_limit", "files", "new_exports", "new_deps", "warnings")
SHA = re.compile(r"^[0-9a-f]{40}$")
GENERATED = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


class ResolveError(Exception):
    """The base could not be resolved. No fallback — main maps it to exit 2."""


# --- values ---------------------------------------------------------------


def _is_int(value: Any) -> bool:
    # bool is an int subclass; `True` must not pass as a line or a count.
    return isinstance(value, int) and not isinstance(value, bool)


def _one_line(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\n" not in value


def _str_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) and v for v in value)


def _hold_value(value: Any) -> bool:
    return value in HOLDS or (isinstance(value, str) and bool(BLAST_RADIUS.match(value)))


# --- findings (reference/findings.md) ----------------------------------------


def _check_locus(f: Dict[str, Any], where: str) -> List[str]:
    if not isinstance(f["file"], str) or not f["file"]:
        return [f"{where}: file must be a path"]
    if not _is_int(f["line"]) or f["line"] < 1:
        return [f"{where}: line must be a positive integer"]
    if not _is_int(f["end_line"]) or f["end_line"] < f["line"]:
        return [f"{where}: end_line must be an integer >= line"]
    return []


def validate_finding(f: Any, where: str) -> List[str]:
    if not isinstance(f, dict):
        return [f"{where}: not an object"]
    errors = [f"{where}: missing {k}" for k in FINDING_REQUIRED if k not in f]
    if errors:
        return errors
    if f["lane"] not in LANES:
        errors.append(f"{where}: lane {f['lane']!r} not in {LANES}")
    unmet = f["action"] == "hold" and f["hold"] == UNMET
    if unmet and any(f[k] is not None for k in ("file", "line", "end_line")):
        errors.append(f"{where}: file, line, end_line must be null for unmet claim")
    if not unmet:
        errors += _check_locus(f, where)
    errors += [f"{where}: {k} must be one non-empty line" for k in ("title", "evidence") if not _one_line(f[k])]
    action = f["action"]
    if action not in ACTIONS:
        errors.append(f"{where}: action {action!r} not in {ACTIONS}")
        return errors
    if action in TARGETLESS and f["target"] is not None:
        errors.append(f"{where}: target must be null for {action}")
    if action not in TARGETLESS and not _one_line(f["target"]):
        errors.append(f"{where}: target must be path:line for {action}")
    if not _str_list(f["concepts"]):
        errors.append(f"{where}: concepts must be a list of strings")
    elif action == "hold" and f["concepts"]:
        errors.append(f"{where}: concepts must be empty for hold")
    if action == "hold":
        if not _hold_value(f["hold"]):
            errors.append(f"{where}: hold {f['hold']!r} is not a value reference/ghost.md lists")
        if not _one_line(f.get("next")):
            errors.append(f"{where}: next must be one line on hold")
        claim = f.get("claim")
        if claim is not None and not _is_int(claim):
            errors.append(f"{where}: claim must be an integer or null")
        if f["hold"] in CLAIMED and claim is None:
            errors.append(f"{where}: claim is required for {f['hold']}")
    elif f["hold"] is not None:
        errors.append(f"{where}: hold must be null unless action is hold")
    return errors


def parse_reply(text: str) -> Any:
    """One code fence around the whole reply is transport; strip it, nothing more."""
    text = text.strip()
    fence = re.match(r"^```[a-zA-Z]*\n(.*)\n```$", text, re.S)
    return json.loads(fence.group(1) if fence else text)


def validate_findings(data: Any) -> List[str]:
    if not isinstance(data, list):
        return ["reply is not a JSON array"]
    return [e for i, f in enumerate(data) for e in validate_finding(f, f"[{i}]")]


# --- report (reference/report.md) ------------------------------------------


def _check_version(report: Dict[str, Any]) -> List[str]:
    value = report.get("contract_version")
    if not _is_int(value):
        return ["contract_version must be an integer"]
    if value != CONTRACT_VERSION:
        return [f"contract_version {value} does not match contract version {CONTRACT_VERSION} (exact match, no negotiation)"]
    return []


def _check_intent(intent: Any) -> List[str]:
    if not isinstance(intent, dict):
        return ["intent must be an object"]
    errors = []
    if intent.get("source") not in INTENT_SOURCES:
        errors.append(f"intent.source {intent.get('source')!r} not in {INTENT_SOURCES}")
    pr = intent.get("pr", "missing")
    if intent.get("source") == "pr" and not (_is_int(pr) and pr > 0):
        errors.append("intent.pr must be the PR number when intent.source is pr")
    if intent.get("source") != "pr" and pr is not None:
        errors.append("intent.pr must be null unless intent.source is pr")
    return errors


def _check_claims(claims: Any) -> List[str]:
    if not isinstance(claims, list) or not claims:
        return ["claims must be a non-empty list"]
    errors = [
        f"claims[{i}]: needs integer n and one-line text"
        for i, c in enumerate(claims)
        if not (isinstance(c, dict) and _is_int(c.get("n")) and _one_line(c.get("text")))
    ]
    numbers = [c.get("n") for c in claims if isinstance(c, dict)]
    if len(set(numbers)) != len(numbers):
        errors.append("claims: duplicate n")
    return errors


def _check_scope(scope: Any) -> List[str]:
    if not isinstance(scope, dict):
        return ["scope must be an object"]
    errors = [f"scope: missing {k}" for k in SCOPE_REQUIRED if k not in scope]
    if errors:
        return errors
    if not _one_line(scope["base_ref"]):
        errors.append("scope.base_ref must be one line")
    errors += [f"scope.{k} must be a 40-char sha" for k in ("base_sha", "head_sha") if not SHA.match(str(scope[k]))]
    if scope["source"] not in BASE_SOURCES:
        errors.append(f"scope.source {scope['source']!r} not in {BASE_SOURCES}")
    if not isinstance(scope["includes_worktree"], bool):
        errors.append("scope.includes_worktree must be a boolean")
    if not _is_int(scope["hunks"]) or scope["hunks"] < 1:
        errors.append("scope.hunks must be a positive integer — an empty diff writes no report")
    return errors


def _check_lanes(lanes: Any, single_pass: Any) -> List[str]:
    if not isinstance(lanes, dict) or sorted(lanes) != sorted(LANES):
        return [f"lanes must have exactly the keys {LANES}"]
    errors = [f"lanes.{k} {v!r} not in {LANE_STATUSES}" for k, v in lanes.items() if v not in LANE_STATUSES]
    if not isinstance(single_pass, bool):
        errors.append("single_pass must be a boolean")
    return errors


def _check_also(f: Dict[str, Any], where: str, reported: List[str]) -> List[str]:
    also = f.get("also")
    if not isinstance(also, list) or any(a not in reported or a == f.get("lane") for a in also):
        return [f"{where}: also must list the other reported lanes dedup merged in"]
    return []


def _check_applied(applied: Any, reported: List[str]) -> List[str]:
    if not isinstance(applied, list):
        return ["applied must be a list"]
    errors: List[str] = []
    for i, f in enumerate(applied):
        where = f"applied[{i}]"
        errors += validate_finding(f, where)
        if not isinstance(f, dict):
            continue
        if f.get("action") == "hold":
            errors.append(f"{where}: a hold belongs in held")
        errors += _check_also(f, where, reported)
        if f.get("status") not in APPLY_STATUSES:
            errors.append(f"{where}: status {f.get('status')!r} not in {APPLY_STATUSES}")
        if not _one_line(f.get("outcome")):
            errors.append(f"{where}: outcome must be one line")
        elif f.get("status") == "skipped" and not f["outcome"].startswith("skipped: "):
            errors.append(f"{where}: a skipped outcome reads 'skipped: <why>'")
    return errors


def _check_held(held: Any, claim_numbers: List[Any], reported: List[str]) -> List[str]:
    if not isinstance(held, list):
        return ["held must be a list"]
    errors: List[str] = []
    for i, f in enumerate(held):
        where = f"held[{i}]"
        errors += validate_finding(f, where)
        if not isinstance(f, dict):
            continue
        if f.get("action") != "hold":
            errors.append(f"{where}: action must be hold")
        errors += _check_also(f, where, reported)
        if "claim" not in f:
            errors.append(f"{where}: missing claim")
        elif f["claim"] is not None and f["claim"] not in claim_numbers:
            errors.append(f"{where}: claim {f['claim']!r} is not in claims")
    return errors


def _check_concepts(report: Dict[str, Any]) -> List[str]:
    removed, kept = report["concepts_removed"], report["concepts_kept"]
    errors: List[str] = []
    if not _str_list(removed) or len(set(removed)) != len(removed):
        errors.append("concepts_removed must be a list of unique strings")
    elif isinstance(report["applied"], list):
        done = {
            c for f in report["applied"]
            if isinstance(f, dict) and f.get("status") == "applied" and isinstance(f.get("concepts"), list)
            for c in f["concepts"]
        }
        if set(removed) != done:
            errors.append("concepts_removed must equal the concepts of applied findings with status applied")
    if not isinstance(kept, list):
        errors.append("concepts_kept must be a list")
    else:
        errors += [
            f"concepts_kept[{i}]: needs name and a non-negative integer callers"
            for i, k in enumerate(kept)
            if not (isinstance(k, dict) and _one_line(k.get("name")) and _is_int(k.get("callers")) and k["callers"] >= 0)
        ]
    return errors


def _check_checks(checks: Any) -> List[str]:
    if not isinstance(checks, list):
        return ["checks must be a list"]
    errors: List[str] = []
    for i, c in enumerate(checks):
        where = f"checks[{i}]"
        if not isinstance(c, dict) or not _one_line(c.get("name")):
            errors.append(f"{where}: needs name, the command as run")
            continue
        if c.get("outcome") not in CHECK_OUTCOMES:
            errors.append(f"{where}: outcome {c.get('outcome')!r} not in {CHECK_OUTCOMES}")
        elif c["outcome"] == "pass" and c.get("detail", "missing") is not None:
            errors.append(f"{where}: detail must be null on pass")
        elif c["outcome"] == "fail" and not _one_line(c.get("detail")):
            errors.append(f"{where}: detail must be the first failing line on fail")
    return errors


def _check_tripwires(tripwires: Any, justifications: Any) -> List[str]:
    if not isinstance(tripwires, dict):
        return ["tripwires must be tripwires.py's JSON object"]
    errors = [f"tripwires: missing {k}" for k in TRIPWIRES_REQUIRED if k not in tripwires]
    if errors:
        return errors
    errors += [f"tripwires.{k} must be an integer" for k in ("added", "removed", "changed", "loc_limit") if not _is_int(tripwires[k])]
    files = tripwires["files"]
    if not isinstance(files, dict) or not _is_int(files.get("changed")) or not all(
        isinstance(files.get(k), list) for k in ("added", "deleted")
    ):
        errors.append("tripwires.files needs changed, added, deleted")
    errors += [f"tripwires.{k} must be a list" for k in ("new_exports", "new_deps") if not isinstance(tripwires[k], list)]
    warnings = tripwires["warnings"]
    if not _str_list(warnings):
        errors.append("tripwires.warnings must be a list of strings")
        return errors
    if not isinstance(justifications, list) or not all(
        isinstance(j, dict) and isinstance(j.get("warning"), str) and _one_line(j.get("note")) for j in justifications
    ):
        errors.append("justifications: each needs warning and a one-line note")
        return errors
    named = [j["warning"] for j in justifications]
    errors += [f"justifications: none for warning {w!r}" for w in warnings if named.count(w) != 1]
    errors += [f"justifications: {w!r} is not a tripwires warning" for w in named if w not in warnings]
    return errors


def _check_out_of_intent(files: Any, lanes: Any) -> List[str]:
    if not isinstance(lanes, dict) or lanes.get("trace") != "reported":
        return [] if files is None else ["out_of_intent_files must be null when the trace lane did not report"]
    if not _str_list(files) or files != sorted(set(files)):
        return ["out_of_intent_files must be a sorted list of unique paths when the trace lane reported"]
    return []


def validate(report: Any) -> List[str]:
    if not isinstance(report, dict):
        return ["report must be a JSON object"]
    errors = _check_version(report)
    missing = [f"missing {k}" for k in REPORT_REQUIRED if k not in report]
    if missing:
        return errors + missing
    if not isinstance(report["generated"], str) or not GENERATED.match(report["generated"]):
        errors.append("generated must be UTC ISO, YYYY-MM-DDTHH:MM:SSZ")
    if not _one_line(report["branch"]):
        errors.append("branch must be one line")
    claims = report["claims"]
    claim_numbers = [c.get("n") for c in claims if isinstance(c, dict)] if isinstance(claims, list) else []
    lanes = report["lanes"]
    reported = [k for k in LANES if isinstance(lanes, dict) and lanes.get(k) == "reported"]
    errors += _check_intent(report["intent"])
    errors += _check_claims(claims)
    errors += _check_scope(report["scope"])
    errors += _check_lanes(report["lanes"], report["single_pass"])
    errors += _check_applied(report["applied"], reported)
    errors += _check_held(report["held"], claim_numbers, reported)
    errors += _check_out_of_intent(report["out_of_intent_files"], report["lanes"])
    errors += _check_concepts(report)
    errors += _check_checks(report["checks"])
    errors += _check_tripwires(report["tripwires"], report["justifications"])
    return errors


# --- merge (commands/exorcise.md §3-§4) ---------------------------------------


def out_of_intent_files(trace: List[Dict[str, Any]]) -> List[str]:
    """Files carrying a trace revert or trust-boundary hold, from the raw reply: before
    dedup (a hold elsewhere can absorb the revert) and before apply (apply erases it)."""
    return sorted({
        f["file"] for f in trace
        if f["action"] == "revert" or (f["action"] == "hold" and f["hold"] in OUT_OF_INTENT_HOLDS)
    })


def _same(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    if a["hold"] == UNMET or b["hold"] == UNMET:
        return a["hold"] == b["hold"] == UNMET and a.get("claim") == b.get("claim")
    same_target = a["lane"] != b["lane"] and a["target"] is not None and a["target"] == b["target"]
    return (a["file"], a["line"]) == (b["file"], b["line"]) or same_target


def dedup(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Findings on the same file + line, the same target from two lanes, or the same unmet
    claim are one finding: the highest-precedence action survives, in reply order, and
    records the other lanes in `also`. One lane's findings on one target at two loci are
    two edits."""
    ranked = sorted(enumerate(findings), key=lambda p: (PRECEDENCE.index(p[1]["action"]), p[0]))
    kept: List[Tuple[int, Dict[str, Any]]] = []
    for i, f in ranked:
        winner = next((w for _, w in kept if _same(w, f)), None)
        if winner is None:
            kept.append((i, {**f, "also": []}))
        elif f["lane"] != winner["lane"] and f["lane"] not in winner["also"]:
            winner["also"].append(f["lane"])
    return [f for _, f in sorted(kept, key=lambda p: p[0])]


def _read_lane(path: Path) -> Tuple[List[str], Optional[List[Dict[str, Any]]]]:
    """A lane's findings, or the errors that make it a lane that did not report."""
    try:
        data = parse_reply(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"does not parse: {exc}"], None
    errors = validate_findings(data)
    if not errors:
        errors = [f"[{i}]: lane {f['lane']!r} in the {path.stem} reply" for i, f in enumerate(data) if f["lane"] != path.stem]
    return errors, None if errors else data


def merge(
    lane_files: List[Path], tripwires: Dict[str, Any], scope: Dict[str, Any], single_pass: bool
) -> Tuple[Dict[str, Any], Dict[str, List[str]]]:
    """The report draft: lanes, deduped findings, out_of_intent_files, tripwires. Keys
    that need judgment are left null for the command; `validate` names any it misses."""
    lanes = dict.fromkeys(LANES, "did not report")
    found: Dict[str, List[Dict[str, Any]]] = {}
    errors: Dict[str, List[str]] = {}
    for path in lane_files:
        if path.stem not in LANES:
            errors[path.stem] = [f"{path.name} is not a lane: name it {'|'.join(LANES)}.json"]
            continue
        lane_errors, data = _read_lane(path)
        if lane_errors:
            errors[path.stem] = lane_errors
            continue
        lanes[path.stem] = "reported"
        found[path.stem] = data
    merged = dedup([f for lane in LANES for f in found.get(lane, [])])
    draft = {
        "contract_version": CONTRACT_VERSION,
        "generated": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "branch": None,
        "intent": None,
        "claims": None,
        "scope": scope,
        "lanes": lanes,
        "single_pass": single_pass,
        "concepts_removed": None,
        "concepts_kept": None,
        "applied": [{**f, "status": None, "outcome": None} for f in merged if f["action"] != "hold"],
        "held": [{"claim": None, **f} for f in merged if f["action"] == "hold"],
        "out_of_intent_files": out_of_intent_files(found["trace"]) if "trace" in found else None,
        "checks": None,
        "tripwires": tripwires,
        "justifications": None,
    }
    return draft, errors


# --- base (commands/exorcise.md §2) ------------------------------------------


def _git(args: List[str], cwd: Optional[str]) -> Optional[str]:
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    return done.stdout.strip() if done.returncode == 0 else None


def _commit(ref: str, cwd: Optional[str]) -> Optional[str]:
    return _git(["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], cwd)


def _merge_base(sha: str, cwd: Optional[str]) -> str:
    base = _git(["merge-base", sha, "HEAD"], cwd)
    if base is None:
        raise ResolveError(f"no merge-base between {sha} and HEAD")
    return base


def resolve_base(base: Optional[str] = None, pr_base: Optional[str] = None, cwd: Optional[str] = None) -> Dict[str, str]:
    """--base, else the PR's base, else @{upstream} → main → HEAD~1. base_sha is
    always the merge-base with HEAD: the diff is three-dot, and §5 reads BASE."""
    if _commit("HEAD", cwd) is None:
        raise ResolveError("HEAD does not resolve to a commit")
    if base is not None:
        tip = _commit(base, cwd)
        if tip is None:
            raise ResolveError(f"--base {base} does not resolve to a commit")
        if pr_base is not None:
            pr_tip = _commit(pr_base, cwd)
            if pr_tip != tip:
                raise ResolveError(f"--base {base} is {tip}; the PR's base is {pr_tip or pr_base}")
            return {"base_sha": _merge_base(tip, cwd), "base_ref": pr_base, "source": "pr"}
        return {"base_sha": _merge_base(tip, cwd), "base_ref": base, "source": "flag"}
    if pr_base is not None:
        tip = _commit(pr_base, cwd)
        if tip is None:
            raise ResolveError(f"the PR's base {pr_base} is not in this clone — fetch it")
        return {"base_sha": _merge_base(tip, cwd), "base_ref": pr_base, "source": "pr"}
    upstream = _git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], cwd)
    for ref, source in ((upstream, "upstream"), ("main", "main"), ("HEAD~1", "head~1")):
        tip = _commit(ref, cwd) if ref else None
        merge_base = _git(["merge-base", tip, "HEAD"], cwd) if tip else None
        if merge_base:
            return {"base_sha": merge_base, "base_ref": str(ref), "source": source}
    raise ResolveError("no base: no upstream, no main, and HEAD is a root commit — pass --base")


# --- shell --------------------------------------------------------------------


def _print_errors(head: str, errors: List[str]) -> None:
    print(head)
    for e in errors:
        print(f"  - {e}")


def _merge(args: argparse.Namespace) -> int:
    try:
        tripwires = json.loads(Path(args.tripwires).read_text(encoding="utf-8"))
        scope = json.loads(Path(args.scope).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"merge: {exc}")
        return 1
    draft, errors = merge([Path(p) for p in args.lanes], tripwires, scope, args.single_pass)
    for lane, lane_errors in errors.items():
        _print_errors(f"{lane}: did not report —", lane_errors)
    Path(args.out).write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    files = draft["out_of_intent_files"]
    print(
        f"{len(draft['applied'])} to apply, {len(draft['held'])} held → {args.out}"
        + f" · out of intent: {'n/a' if files is None else len(files)} file(s)"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resolve-base")
    r.add_argument("--base")
    r.add_argument("--pr-base")
    sub.add_parser("findings").add_argument("path")
    m = sub.add_parser("merge")
    m.add_argument("out")
    m.add_argument("lanes", nargs="+")
    m.add_argument("--tripwires", required=True)
    m.add_argument("--scope", required=True)
    m.add_argument("--single-pass", action="store_true")
    sub.add_parser("validate").add_argument("path")
    args = parser.parse_args()

    if args.cmd == "merge":
        return _merge(args)

    if args.cmd == "resolve-base":
        try:
            print(json.dumps(resolve_base(args.base, args.pr_base)))
        except ResolveError as exc:
            print(f"resolve-base: {exc}", file=sys.stderr)
            return 2
        return 0

    try:
        text = Path(args.path).read_text(encoding="utf-8")
        data = parse_reply(text) if args.cmd == "findings" else json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"{args.path}: does not parse: {exc}")
        return 1
    if args.cmd == "findings":
        errors = validate_findings(data)
        if errors:
            _print_errors("Findings invalid — the lane did not report:", errors)
            return 1
        print(f"Findings valid: {len(data)} finding(s).")
        return 0
    errors = validate(data)
    if errors:
        _print_errors("Report invalid — not written:", errors)
        return 1
    print(f"Report valid: contract {CONTRACT_VERSION}, {len(data['applied'])} applied, {len(data['held'])} held.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
