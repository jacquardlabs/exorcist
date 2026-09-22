#!/usr/bin/env python3
"""Unit tests for scripts/report.py. Self-running: prints OK."""
import copy
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import report  # noqa: E402

BASE_SHA = "6a528f8c0d1e4b2f9a7c3e5d1b0a9f8e7d6c5b4a"
HEAD_SHA = "c0ffee1234567890abcdef1234567890abcdef12"
WARNINGS = ["243 lines changed (+212/-31); warn at 200", "1 new file(s): src/util/backoff.ts"]


def _finding(**over):
    f = {
        "lane": "abstraction",
        "file": "src/http/client.ts",
        "line": 44,
        "end_line": 71,
        "title": "RetryPolicy class, 1 caller",
        "evidence": "grep -n RetryPolicy src/ → 2 hits: the definition and sendWebhook",
        "action": "inline",
        "target": "src/webhook/sender.ts:30",
        "concepts": ["RetryPolicy"],
        "hold": None,
    }
    f.update(over)
    return f


def _hold(**over):
    over = {
        "lane": "trace", "file": "tests/test_sender.py", "line": 88, "end_line": 120,
        "title": "give-up test for sendWebhook", "evidence": "claim 3 names the give-up path",
        "action": "hold", "target": None, "concepts": [], "hold": "implied by intent",
        "claim": 3, "next": "nothing; kept because claim 3 entails it", **over,
    }
    return _finding(**over)


def _report():
    return {
        "contract_version": 1,
        "generated": "2026-09-22T18:04:11Z",
        "branch": "studious/build-42-retry",
        "intent": {"source": "text", "pr": None},
        "claims": [
            {"n": 1, "text": "sendWebhook retries a failed POST up to 3 times with backoff"},
            {"n": 3, "text": "tests cover the retry and give-up paths in tests/test_sender.py"},
        ],
        "scope": {
            "base_ref": "main", "base_sha": BASE_SHA, "head_sha": HEAD_SHA,
            "source": "flag", "includes_worktree": True, "hunks": 9,
        },
        "lanes": {"trace": "reported", "abstraction": "reported", "threshold": "reported", "deletion": "did not report"},
        "single_pass": False,
        "concepts_removed": ["RetryPolicy"],
        "concepts_kept": [{"name": "backoff_delays", "callers": 2}],
        "applied": [
            {**_finding(), "also": [], "status": "applied", "outcome": "inlined into sendWebhook"},
            {
                **_finding(lane="trace", file="src/util/format.ts", line=3, end_line=40, title="reformatted formatDate",
                           action="revert", target=None, concepts=["formatDate"]),
                "also": [], "status": "skipped", "outcome": "skipped: a snapshot pins the new formatting",
            },
        ],
        "held": [{**_hold(), "also": ["deletion"]}],
        "checks": [
            {"name": "npm test -- tests/test_sender.py", "outcome": "pass", "detail": None},
            {"name": "npx tsc --noEmit", "outcome": "fail", "detail": "src/x.ts(3,1): error TS2304"},
        ],
        "tripwires": {
            "added": 212, "removed": 31, "changed": 243, "loc_limit": 200,
            "files": {"changed": 5, "added": ["src/util/backoff.ts"], "deleted": []},
            "new_exports": [], "new_deps": [], "warnings": list(WARNINGS),
        },
        "justifications": [{"warning": w, "note": "the tests claim 3 requires"} for w in WARNINGS],
    }


def _errors_with(mutate):
    r = _report()
    mutate(r)
    return report.validate(r)


# --- report schema ------------------------------------------------------------


def test_valid_report_passes():
    assert report.validate(_report()) == []


def test_each_required_key_missing_fails():
    for key in report.REPORT_REQUIRED:
        r = _report()
        del r[key]
        errors = report.validate(r)
        assert errors, key
        assert any(key in e for e in errors), (key, errors)
    for key in report.SCOPE_REQUIRED:
        assert any(key in e for e in _errors_with(lambda r, k=key: r["scope"].pop(k))), key
    for key in report.TRIPWIRES_REQUIRED:
        assert any(key in e for e in _errors_with(lambda r, k=key: r["tripwires"].pop(k))), key


def test_contract_version_is_an_exact_int():
    for bad in (True, "1", 1.0, None):
        assert "contract_version must be an integer" in _errors_with(lambda r, v=bad: r.update(contract_version=v)), bad
    errors = _errors_with(lambda r: r.update(contract_version=2))
    assert "contract_version 2 does not match contract version 1 (exact match, no negotiation)" in errors, errors


def test_bad_enums_fail():
    cases = {
        "scope.source": lambda r: r["scope"].update(source="upstreamish"),
        "intent.source": lambda r: r["intent"].update(source="guess"),
        "lanes.trace": lambda r: r["lanes"].update(trace="silent"),
        "status": lambda r: r["applied"][0].update(status="done"),
        "outcome": lambda r: r["checks"][0].update(outcome="ok"),
        "action": lambda r: r["applied"][0].update(action="rewrite"),
        "hold": lambda r: r["held"][0].update(hold="taste"),
        "lane": lambda r: r["applied"][0].update(lane="deadcode"),
    }
    for needle, mutate in cases.items():
        errors = _errors_with(mutate)
        assert any(needle in e for e in errors), (needle, errors)


def test_lanes_need_exactly_the_four_and_single_pass_reports_all():
    assert _errors_with(lambda r: r["lanes"].pop("deletion"))
    assert any("single_pass" in e for e in _errors_with(lambda r: r.update(single_pass=True)))


def test_concepts_removed_matches_applied():
    assert _errors_with(lambda r: r.update(concepts_removed=["RetryPolicy", "formatDate"]))  # formatDate was skipped
    assert _errors_with(lambda r: r.update(concepts_removed=[]))
    assert _errors_with(lambda r: r["concepts_kept"][0].update(callers=-1))


def test_held_carries_claim_and_next():
    assert any("claim 9" in e for e in _errors_with(lambda r: r["held"][0].update(claim=9)))
    assert any("claim is required" in e for e in _errors_with(lambda r: r["held"][0].update(claim=None)))
    assert any("missing claim" in e for e in _errors_with(lambda r: r["held"][0].pop("claim")))
    assert any("next" in e for e in _errors_with(lambda r: r["held"][0].update(next="")))
    tb = {**_hold(hold="trust boundary", claim=None), "also": []}
    assert _errors_with(lambda r: r["held"].append(tb)) == []
    assert any("belongs in held" in e for e in _errors_with(lambda r: r["applied"].append({**tb, "status": "applied", "outcome": "x"})))


def test_also_and_skip_outcome_and_checks_detail():
    assert _errors_with(lambda r: r["held"][0].update(also=["trace"]))  # its own lane
    assert _errors_with(lambda r: r["applied"][1].update(outcome="left it"))
    assert _errors_with(lambda r: r["checks"][0].update(detail="noise"))
    assert _errors_with(lambda r: r["checks"][1].update(detail=None))


def test_justifications_match_warnings_exactly():
    assert any("none for warning" in e for e in _errors_with(lambda r: r["justifications"].pop()))
    assert any("not a tripwires warning" in e for e in _errors_with(lambda r: r["justifications"][0].update(warning="243 lines")))
    assert _errors_with(lambda r: r["justifications"].append(copy.deepcopy(r["justifications"][0])))


def test_scope_shas_and_hunks():
    assert _errors_with(lambda r: r["scope"].update(base_sha="6a528f8"))
    assert _errors_with(lambda r: r["scope"].update(hunks=0))
    assert _errors_with(lambda r: r["scope"].update(includes_worktree="yes"))
    assert _errors_with(lambda r: r.update(generated="2026-09-22 18:04"))


def test_intent_pr_pairing():
    assert _errors_with(lambda r: r["intent"].update(source="pr"))
    assert _errors_with(lambda r: r["intent"].update(pr=12))
    assert report.validate({**_report(), "intent": {"source": "pr", "pr": 12}}) == []


# --- lane findings -------------------------------------------------------------


def test_findings_valid_and_empty():
    assert report.validate_findings([_finding(), _hold()]) == []
    assert report.validate_findings([]) == []
    assert report.validate_findings({"findings": []}) == ["reply is not a JSON array"]


def test_findings_malformed_fail():
    cases = [
        _finding(file=None),  # a revert with no file
        _finding(line=True),
        _finding(end_line=10),
        _finding(target=None),
        _finding(action="revert"),  # target must be null
        _finding(evidence=""),
        _finding(title="two\nlines"),
        _finding(hold="public API"),  # hold on a non-hold
        _hold(hold=None),  # a hold with no hold value
        _hold(concepts=["x"]),
        _hold(next=None),
        _hold(claim=None),  # implied by intent needs its claim
    ]
    for f in cases:
        assert report.validate_findings([f]), f
    for key in report.FINDING_REQUIRED:
        f = _finding()
        del f[key]
        assert report.validate_findings([f]) == [f"[0]: missing {key}"], key


def test_blast_radius_hold_value():
    assert report.validate_findings([_hold(hold="blast radius: 3 consumers outside the diff", claim=None)]) == []
    assert report.validate_findings([_hold(hold="blast radius: many", claim=None)])


def test_parse_reply_strips_one_fence_only():
    assert report.parse_reply("```json\n[]\n```") == []
    for bad in ("Here: []", "```json\n```json\n[]\n```\n```"):
        try:
            report.parse_reply(bad)
        except json.JSONDecodeError:
            continue
        raise AssertionError(bad)


def test_holds_match_ghost_md():
    text = (REPO / "reference" / "ghost.md").read_text(encoding="utf-8")
    paragraph = text.split("**`hold` is for the real ones you must not touch.**", 1)[1].split("\n- ", 1)[0]
    values = [" ".join(v.split()) for v in re.findall(r"`([^`]+)`", paragraph)]  # values wrap lines
    fixed = tuple(v for v in values if not v.startswith("blast radius"))
    assert fixed == report.HOLDS, (fixed, report.HOLDS)
    assert any(report.BLAST_RADIUS.match(v.replace("N", "3")) for v in values if v.startswith("blast radius"))


def test_tripwires_output_validates():
    import tripwires

    diff = "--- /dev/null\n+++ b/src/x.py\n@@ -0,0 +1,2 @@\n+def backoff():\n+    return 1\n"
    out = json.loads(json.dumps(tripwires.analyze(diff)))
    assert out["warnings"] and out["new_exports"], out
    assert report._check_tripwires(out, [{"warning": w, "note": "n"} for w in out["warnings"]]) == []


def test_report_md_example_validates():
    text = (REPO / "reference" / "report.md").read_text(encoding="utf-8")
    example = json.loads(re.search(r"```json\n(.*?)\n```", text, re.S).group(1))
    assert report.validate(example) == []
    assert sorted(example) == sorted(report.REPORT_REQUIRED)


def test_cli_validate_exit_codes():
    with tempfile.TemporaryDirectory() as tmp:
        good, bad = Path(tmp) / "good.json", Path(tmp) / "bad.json"
        good.write_text(json.dumps(_report()))
        bad.write_text(json.dumps({**_report(), "contract_version": 2}))
        run = [sys.executable, str(REPO / "scripts" / "report.py")]
        assert subprocess.run([*run, "validate", str(good)], capture_output=True, check=False).returncode == 0
        assert subprocess.run([*run, "validate", str(bad)], capture_output=True, check=False).returncode == 1
        lane = Path(tmp) / "trace.json"
        lane.write_text("```json\n" + json.dumps([_hold()]) + "\n```")
        assert subprocess.run([*run, "findings", str(lane)], capture_output=True, check=False).returncode == 0
        lane.write_text("I found nothing.")
        assert subprocess.run([*run, "findings", str(lane)], capture_output=True, check=False).returncode == 1


# --- base resolution --------------------------------------------------------------


def _git(cwd, *args):
    done = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
        cwd=cwd, capture_output=True, text=True, check=True,
    )
    return done.stdout.strip()


def _repo(tmp, branch="main"):
    _git(tmp, "init", "-q")
    _git(tmp, "symbolic-ref", "HEAD", f"refs/heads/{branch}")
    return tmp


def _commit(cwd, name):
    (Path(cwd) / name).write_text(name)
    _git(cwd, "add", name)
    _git(cwd, "commit", "-q", "-m", name)
    return _git(cwd, "rev-parse", "HEAD")


def _raises(fn):
    try:
        fn()
    except report.ResolveError:
        return True
    return False


def test_resolve_base_flag_is_the_merge_base():
    with tempfile.TemporaryDirectory() as tmp:
        fork = _commit(_repo(tmp), "a")
        _git(tmp, "checkout", "-q", "-b", "feature")
        _commit(tmp, "b")
        _git(tmp, "checkout", "-q", "main")
        tip = _commit(tmp, "c")  # main moves past the fork point
        _git(tmp, "checkout", "-q", "feature")
        got = report.resolve_base("main", cwd=tmp)
        assert got == {"base_sha": fork, "base_ref": "main", "source": "flag"}, got
        assert got["base_sha"] != tip
        assert _raises(lambda: report.resolve_base("no-such-ref", cwd=tmp))


def test_resolve_base_pr_conflict_and_agreement():
    with tempfile.TemporaryDirectory() as tmp:
        a = _commit(_repo(tmp), "a")
        b = _commit(tmp, "b")
        _commit(tmp, "c")
        assert report.resolve_base(pr_base=a, cwd=tmp) == {"base_sha": a, "base_ref": a, "source": "pr"}
        assert report.resolve_base("HEAD~2", pr_base=a, cwd=tmp)["source"] == "pr"
        assert _raises(lambda: report.resolve_base("HEAD~1", pr_base=a, cwd=tmp))
        assert b


def test_resolve_base_chain():
    with tempfile.TemporaryDirectory() as tmp:
        a = _commit(_repo(tmp), "a")
        _git(tmp, "checkout", "-q", "-b", "trunk")
        b = _commit(tmp, "b")
        _git(tmp, "checkout", "-q", "-b", "feature")
        _commit(tmp, "c")
        assert report.resolve_base(cwd=tmp) == {"base_sha": a, "base_ref": "main", "source": "main"}
        _git(tmp, "branch", "-q", "--set-upstream-to=trunk", "feature")
        assert report.resolve_base(cwd=tmp) == {"base_sha": b, "base_ref": "trunk", "source": "upstream"}


def test_resolve_base_head_1_then_root():
    with tempfile.TemporaryDirectory() as tmp:
        a = _commit(_repo(tmp, "trunk"), "a")
        assert _raises(lambda: report.resolve_base(cwd=tmp))  # root commit, no main
        _commit(tmp, "b")
        assert report.resolve_base(cwd=tmp) == {"base_sha": a, "base_ref": "HEAD~1", "source": "head~1"}


def test_cli_resolve_base_exit_2():
    with tempfile.TemporaryDirectory() as tmp:
        _commit(_repo(tmp), "a")
        done = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "report.py"), "resolve-base", "--base", "nope"],
            cwd=tmp, capture_output=True, text=True, check=False,
        )
        assert done.returncode == 2 and "nope" in done.stderr and done.stdout == "", done


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("OK")
