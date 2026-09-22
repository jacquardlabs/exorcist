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
        "held": [{**_hold(), "also": ["abstraction"]}],
        "out_of_intent_files": ["src/util/format.ts"],
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
    # Each needle carries the bad value: only that value's enum check can produce it.
    cases = {
        "scope.source 'upstreamish' not in": lambda r: r["scope"].update(source="upstreamish"),
        "intent.source 'guess' not in": lambda r: r["intent"].update(source="guess"),
        "lanes.trace 'silent' not in": lambda r: r["lanes"].update(trace="silent"),
        "applied[0]: status 'done' not in": lambda r: r["applied"][0].update(status="done"),
        "checks[0]: outcome 'ok' not in": lambda r: r["checks"][0].update(outcome="ok"),
        "action 'rewrite' not in": lambda r: r["applied"][0].update(action="rewrite"),
        "hold 'taste' is not a value": lambda r: r["held"][0].update(hold="taste"),
        "lane 'deadcode' not in": lambda r: r["applied"][0].update(lane="deadcode"),
    }
    for needle, mutate in cases.items():
        errors = _errors_with(mutate)
        assert any(needle in e for e in errors), (needle, errors)


def test_lanes_need_exactly_the_four_and_single_pass_may_miss_one():
    assert _errors_with(lambda r: r["lanes"].pop("deletion"))
    assert _errors_with(lambda r: r.update(single_pass=True)) == []  # deletion did not report
    assert any("single_pass" in e for e in _errors_with(lambda r: r.update(single_pass="yes")))


def test_concepts_removed_matches_applied():
    assert _errors_with(lambda r: r.update(concepts_removed=["RetryPolicy", "formatDate"]))  # formatDate was skipped
    assert _errors_with(lambda r: r.update(concepts_removed=[]))
    assert _errors_with(lambda r: r["concepts_kept"][0].update(callers=-1))
    dup = _errors_with(lambda r: r.update(concepts_removed=["RetryPolicy", "RetryPolicy"]))
    assert "concepts_removed must be a list of unique strings" in dup, dup
    assert "concepts_removed must be a list of unique strings" in _errors_with(lambda r: r.update(concepts_removed=[["x"]]))


def test_claims_shape():
    for bad in (None, [], {"n": 1}):
        assert "claims must be a non-empty list" in _errors_with(lambda r, v=bad: r.update(claims=v)), bad
    for bad in ({"n": True, "text": "t"}, {"n": "1", "text": "t"}, {"n": 2, "text": "two\nlines"}, {"n": 2}, "claim 2"):
        errors = _errors_with(lambda r, v=bad: r["claims"].append(v))
        assert "claims[2]: needs integer n and one-line text" in errors, (bad, errors)
    assert "claims: duplicate n" in _errors_with(lambda r: r["claims"].append({"n": 1, "text": "again"}))


def test_unhashable_values_are_errors_not_type_errors():
    errors = _errors_with(lambda r: r["claims"].append({"n": [2], "text": "t"}))
    assert "claims[2]: needs integer n and one-line text" in errors and "claims: duplicate n" not in errors, errors
    for bad in ([["RetryPolicy"]], [{}]):
        errors = _errors_with(lambda r, v=bad: r["applied"][0].update(concepts=v))
        assert "applied[0]: concepts must be a list of strings" in errors, (bad, errors)


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
    assert any("reported lanes" in e for e in _errors_with(lambda r: r["held"][0].update(also=["deletion"])))  # did not report
    assert _errors_with(lambda r: r["applied"][1].update(outcome="left it"))
    assert _errors_with(lambda r: r["checks"][0].update(detail="noise"))
    assert _errors_with(lambda r: r["checks"][1].update(detail=None))


def test_justifications_match_warnings_exactly():
    assert any("none for warning" in e for e in _errors_with(lambda r: r["justifications"].pop()))
    assert any("not a tripwires warning" in e for e in _errors_with(lambda r: r["justifications"][0].update(warning="243 lines")))
    assert _errors_with(lambda r: r["justifications"].append(copy.deepcopy(r["justifications"][0])))


def test_scope_shas_and_hunks():
    assert _errors_with(lambda r: r["scope"].update(base_sha="6a528f8"))
    sha256 = "a" * 64
    assert _errors_with(lambda r: r["scope"].update(base_sha=sha256, head_sha=sha256)) == []
    for bad in ("a" * 63, "a" * 41, "A" * 64, "a" * 104):
        assert "scope.base_sha must be a 40- or 64-char sha" in _errors_with(lambda r, v=bad: r["scope"].update(base_sha=v)), bad
    assert _errors_with(lambda r: r["scope"].update(hunks=0))
    assert _errors_with(lambda r: r["scope"].update(includes_worktree="yes"))
    assert _errors_with(lambda r: r.update(generated="2026-09-22 18:04"))


def test_intent_pr_pairing():
    assert _errors_with(lambda r: r["intent"].update(source="pr"))
    assert _errors_with(lambda r: r["intent"].update(pr=12))
    assert report.validate({**_report(), "intent": {"source": "pr", "pr": 12}}) == []


def test_out_of_intent_files_pairs_with_the_trace_lane():
    assert _errors_with(lambda r: r.update(out_of_intent_files=[])) == []
    silent = {"trace": "did not report", "abstraction": "reported", "threshold": "reported", "deletion": "reported"}
    assert any("must be null" in e for e in _errors_with(lambda r: r.update(lanes=silent)))
    assert _errors_with(lambda r: r.update(lanes=silent, out_of_intent_files=None)) == []
    assert any("sorted list" in e for e in _errors_with(lambda r: r.update(out_of_intent_files=None)))
    assert _errors_with(lambda r: r.update(out_of_intent_files=["b.ts", "a.ts"]))
    assert _errors_with(lambda r: r.update(out_of_intent_files=["a.ts", "a.ts"]))
    assert _errors_with(lambda r: r.update(out_of_intent_files=3))


def _unmet(**over):
    over = {
        "file": None, "line": None, "end_line": None, "title": "give-up path never records the failure",
        "evidence": "claim 1 → grep -n 'status.*failed' src/webhook/ → 0 hits", "hold": "unmet claim",
        "claim": 1, "next": "implement the failed-status write, or drop claim 1", **over,
    }
    return _hold(**over)


def test_unmet_claim_has_a_null_locus_and_a_claim():
    assert report.validate_findings([_unmet()]) == []
    assert report.validate_findings([_unmet(file="src/x.ts")])
    assert report.validate_findings([_unmet(line=3, end_line=3)])
    assert any("claim is required for unmet claim" in e for e in report.validate_findings([_unmet(claim=None)]))
    assert report.validate_findings([_unmet(concepts=["x"])])
    assert report.validate_findings([_finding(file=None, line=None, end_line=None)])  # only unmet claim may
    assert report.validate_findings([_hold(file=None, line=None, end_line=None)])
    held = {**_unmet(), "also": []}
    assert _errors_with(lambda r: r["held"].append(held)) == []
    assert any("claim 2" in e for e in _errors_with(lambda r: r["held"].append({**held, "claim": 2})))


# --- merge -------------------------------------------------------------------------


def _revert(**over):
    over = {"lane": "trace", "title": "unrequested hunk", "evidence": "claims 1-3: none reaches it",
            "action": "revert", "target": None, "concepts": [], **over}
    return _finding(**over)


def test_out_of_intent_files_derivation():
    assert report.out_of_intent_files([]) == []
    trace = [
        _revert(file="b.ts", line=1, end_line=2),
        _revert(file="b.ts", line=9, end_line=9),  # one file, counted once
        _revert(file="a.ts", line=4, end_line=4),
        _hold(file="c.ts", hold="trust boundary", claim=None),
        _hold(file="d.ts"),  # implied by intent: the ward judged it in intent
        _unmet(),  # no file
        _hold(file="e.ts", hold="spec conflict", claim=None),
    ]
    assert report.out_of_intent_files(trace) == ["a.ts", "b.ts", "c.ts"]


def _lanes(tmp, **replies):
    paths = []
    for lane, reply in replies.items():
        path = Path(tmp) / f"{lane}.json"
        path.write_text(reply if isinstance(reply, str) else json.dumps(reply))
        paths.append(path)
    return paths


def test_merge_holds_a_delete_over_a_test_lead():
    leads = {"leads": [{"value": "inherit", "refs": [
        {"path": "tests/t.sh", "line": 73, "test": True},
        {"path": "CLAUDE.md", "line": 5, "test": False},
    ]}]}
    with tempfile.TemporaryDirectory() as tmp:
        paths = _lanes(tmp, deletion=[
            _finding(lane="deletion", file="tests/t.sh", line=70, end_line=74, action="delete", target=None),
            _finding(lane="deletion", file="CLAUDE.md", line=5, end_line=5, action="delete", target=None),
            _finding(lane="deletion", file="tests/t.sh", line=100, end_line=101, action="delete", target=None),
        ])
        draft, errors = report.merge(paths, {}, {}, False, leads)
    assert not errors, errors
    [held] = draft["held"]
    assert (held["file"], held["hold"], held["target"], held["concepts"]) == ("tests/t.sh", "behavior change", None, []), held
    assert "tests/t.sh:73" in held["next"] and "was delete" in held["evidence"], held
    assert sorted((f["file"], f["line"]) for f in draft["applied"]) == [("CLAUDE.md", 5), ("tests/t.sh", 100)]
    assert report.validate_findings([{k: v for k, v in held.items() if k != "also"}]) == []
    with tempfile.TemporaryDirectory() as tmp:  # no leads → nothing converts
        draft, _ = report.merge(_lanes(tmp, deletion=[_finding(lane="deletion", file="tests/t.sh", line=70,
                                                               end_line=74, action="delete", target=None)]), {}, {}, False)
    assert draft["held"] == [], draft["held"]


def test_merge_counts_before_dedup_and_skips_other_lanes():
    with tempfile.TemporaryDirectory() as tmp:
        shared = {"file": "src/a.ts", "line": 5, "end_line": 9}
        paths = _lanes(
            tmp,
            trace=[_revert(**shared), _unmet()],
            abstraction=[_hold(lane="abstraction", **shared, hold="behavior change", claim=None, next="decide")],
            threshold=[_finding(lane="threshold", file="src/only-threshold.ts", action="delete", target=None)],
            deletion=[
                _revert(lane="deletion", file="src/d.ts"),
                _hold(lane="deletion", file="src/e.ts", hold="trust boundary", claim=None),
            ],
        )
        draft, errors = report.merge(paths, {}, {}, False)
    assert errors == {}, errors
    assert draft["lanes"] == dict.fromkeys(report.LANES, "reported")
    assert draft["out_of_intent_files"] == ["src/a.ts"]  # the hold absorbed the revert; the file still counts
    survivor = next(f for f in draft["held"] if f["file"] == "src/a.ts")
    assert survivor["lane"] == "abstraction" and survivor["also"] == ["trace"], survivor
    assert [f["hold"] for f in draft["held"]] == ["unmet claim", "behavior change", "trust boundary"]  # lane, then reply order
    assert [f["file"] for f in draft["applied"]] == ["src/only-threshold.ts", "src/d.ts"]
    assert draft["applied"][0]["status"] is None


def test_merge_dedups_unmet_claims_by_number():
    with tempfile.TemporaryDirectory() as tmp:
        paths = _lanes(tmp, trace=[_unmet(), _unmet(title="second reading"), _unmet(claim=2)])
        draft, _ = report.merge(paths, {}, {}, False)
    assert [f["claim"] for f in draft["held"]] == [1, 2]


def test_dedup_same_target_across_lanes_only():
    inline = _finding()
    move = _finding(lane="threshold", file="src/other.ts", line=10, end_line=12, action="move")
    merged = report.dedup([move, inline])
    assert len(merged) == 1 and merged[0]["action"] == "inline" and merged[0]["also"] == ["threshold"], merged
    one_lane = [
        _finding(lane="threshold", file="src/a.ts", line=12, end_line=12, action="move", target="src/api/entry.ts:8"),
        _finding(lane="threshold", file="src/b.ts", line=40, end_line=40, action="move", target="src/api/entry.ts:8"),
    ]
    assert [f["file"] for f in report.dedup(one_lane)] == ["src/a.ts", "src/b.ts"]  # two edits, one entry point


def test_dedup_precedence_on_the_same_lines():
    def at(action, lane):
        extra = {"hold": "public API", "claim": None, "next": "decide", "concepts": []} if action == "hold" else {}
        return _finding(lane=lane, action=action, target=None if action in report.TARGETLESS else f"src/{action}.ts:1", **extra)

    for high, low in zip(report.PRECEDENCE, report.PRECEDENCE[1:]):
        merged = report.dedup([at(low, "threshold"), at(high, "deletion")])
        assert [(f["action"], f["also"]) for f in merged] == [(high, ["threshold"])], (high, low, merged)


def test_merge_invalid_or_missing_trace_is_null():
    with tempfile.TemporaryDirectory() as tmp:
        paths = _lanes(tmp, trace=[_revert(file=None)], abstraction="Here are my findings: []")
        draft, errors = report.merge(paths, {}, {}, False)
        assert draft["lanes"]["trace"] == draft["lanes"]["abstraction"] == draft["lanes"]["deletion"] == "did not report"
        assert draft["out_of_intent_files"] is None
        assert sorted(errors) == ["abstraction", "trace"], errors
        paths = _lanes(tmp, trace=[_revert(lane="deletion", file="x.ts")])  # a reply in the wrong lane
        draft, errors = report.merge(paths, {}, {}, False)
        assert draft["lanes"]["trace"] == "did not report" and "trace" in errors


def test_merge_non_utf8_lane_did_not_report():
    with tempfile.TemporaryDirectory() as tmp:
        paths = _lanes(tmp, trace=[_revert(file="x.ts")], abstraction=[])
        paths[0].write_bytes(b"[\xff\xfe]")
        draft, errors = report.merge(paths, {}, {}, False)
        assert draft["lanes"]["trace"] == "did not report" and draft["lanes"]["abstraction"] == "reported", draft["lanes"]
        assert "does not parse" in errors["trace"][0], errors
        run = [sys.executable, str(REPO / "scripts" / "report.py"), "findings", str(paths[0])]
        done = subprocess.run(run, capture_output=True, text=True, check=False)
        assert done.returncode == 1 and "does not parse" in done.stdout, done


def test_merge_cli_non_utf8_tripwires_or_scope_exits_1():
    with tempfile.TemporaryDirectory() as tmp:
        paths = _lanes(tmp, trace=[], abstraction=[], threshold=[], deletion=[])
        good, bad = Path(tmp) / "good.json", Path(tmp) / "bad.json"
        good.write_text("{}")
        bad.write_bytes(b"{\xff}")
        out = Path(tmp) / "report.json"
        for tw, sc in ((bad, good), (good, bad)):
            run = [sys.executable, str(REPO / "scripts" / "report.py"), "merge", str(out), *map(str, paths),
                   "--tripwires", str(tw), "--scope", str(sc)]
            done = subprocess.run(run, capture_output=True, text=True, check=False)
            assert done.returncode == 1 and done.stdout.startswith("merge:") and not out.exists(), done


def test_merge_draft_validates_once_the_command_fills_it():
    base = _report()
    with tempfile.TemporaryDirectory() as tmp:
        paths = _lanes(
            tmp,
            trace=[_revert(file="src/util/format.ts", line=3, end_line=40)],
            abstraction=[_finding()], threshold=[], deletion=[],
        )
        draft, _ = report.merge(paths, base["tripwires"], base["scope"], False)
    missing = report.validate(draft)
    assert any("claims" in e for e in missing) and any("concepts_removed" in e for e in missing), missing
    draft.update({k: base[k] for k in ("branch", "intent", "claims", "concepts_kept", "checks", "justifications")})
    draft["concepts_removed"] = ["RetryPolicy"]
    for f, (status, outcome) in zip(draft["applied"], [("skipped", "skipped: pinned"), ("applied", "inlined")]):
        f.update(status=status, outcome=outcome)
    assert report.validate(draft) == [], report.validate(draft)
    assert draft["out_of_intent_files"] == ["src/util/format.ts"]


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
    assert report.parse_reply("```json\r\n[\r\n]\r\n```\r\n") == []  # a CRLF reply
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


def test_register_md_holds_are_ghost_md_minus_unmet_claim():
    text = (REPO / "reference" / "register.md").read_text(encoding="utf-8")
    paragraph = text.split("- `hold` — ", 1)[1].split("\n- ", 1)[0].split(". `reference/ghost.md`", 1)[0]
    values = [" ".join(v.split()) for v in re.findall(r"`([^`]+)`", paragraph)]
    assert tuple(v for v in values if not v.startswith("blast radius")) == tuple(h for h in report.HOLDS if h != report.UNMET), values
    assert "blast radius: N consumers outside the diff" in values, values


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


def test_cli_merge_writes_the_draft():
    with tempfile.TemporaryDirectory() as tmp:
        paths = _lanes(tmp, trace="```json\n" + json.dumps([_revert(file="x.ts")]) + "\n```", deletion="prose")
        tw, scope, out = Path(tmp) / "tw.json", Path(tmp) / "scope.json", Path(tmp) / "draft.json"
        tw.write_text(json.dumps(_report()["tripwires"]))
        scope.write_text(json.dumps(_report()["scope"]))
        done = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "report.py"), "merge", str(out), *map(str, paths),
             "--tripwires", str(tw), "--scope", str(scope)],
            capture_output=True, text=True, check=False,
        )
        assert done.returncode == 0, done
        assert "deletion: did not report" in done.stdout and "out of intent: 1 file(s)" in done.stdout, done.stdout
        draft = json.loads(out.read_text())
    assert draft["tripwires"] == _report()["tripwires"] and draft["single_pass"] is False
    assert sorted(draft) == sorted(report.REPORT_REQUIRED)


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
        assert report.resolve_base("HEAD~1", pr_base=b, cwd=tmp) == {"base_sha": b, "base_ref": b, "source": "pr"}
        try:
            report.resolve_base("HEAD~1", pr_base=a, cwd=tmp)
        except report.ResolveError as exc:
            assert str(exc) == f"--base HEAD~1 is {b}; the PR's base is {a}", exc
        else:
            raise AssertionError("a --base that names a different commit than the PR's base resolved")


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


def test_resolve_base_upstream_without_merge_base_is_an_error():
    with tempfile.TemporaryDirectory() as tmp:
        _commit(_repo(tmp), "a")
        _git(tmp, "checkout", "-q", "--orphan", "unrelated")
        _commit(tmp, "b")
        _git(tmp, "checkout", "-q", "main")
        _git(tmp, "checkout", "-q", "-b", "feature")
        _commit(tmp, "c")
        _commit(tmp, "d")  # HEAD~1 and main both resolve: a silent fallback would succeed
        _git(tmp, "branch", "-q", "--set-upstream-to=unrelated", "feature")
        try:
            got = report.resolve_base(cwd=tmp)
        except report.ResolveError as exc:
            assert "unrelated" in str(exc) and "HEAD" in str(exc), exc
        else:
            raise AssertionError(f"fell past the configured upstream: {got}")


def test_resolve_base_deleted_upstream_is_an_error():
    with tempfile.TemporaryDirectory() as tmp:
        _commit(_repo(tmp), "a")
        _git(tmp, "branch", "-q", "trunk")
        _git(tmp, "checkout", "-q", "-b", "feature")
        _commit(tmp, "b")
        _git(tmp, "branch", "-q", "--set-upstream-to=trunk", "feature")
        _git(tmp, "branch", "-q", "-D", "trunk")  # main and HEAD~1 still resolve
        try:
            got = report.resolve_base(cwd=tmp)
        except report.ResolveError as exc:
            assert "feature" in str(exc) and "upstream" in str(exc), exc
        else:
            raise AssertionError(f"fell past the deleted upstream: {got}")


def test_resolve_base_without_git_is_a_resolve_error():
    def missing(*_args, **_kwargs):
        raise FileNotFoundError(2, "No such file or directory", "git")

    real, report.subprocess.run = report.subprocess.run, missing
    try:
        assert _raises(lambda: report.resolve_base())
    finally:
        report.subprocess.run = real
    with tempfile.TemporaryDirectory() as tmp:
        done = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "report.py"), "resolve-base"],
            cwd=tmp, env={"PATH": tmp}, capture_output=True, text=True, check=False,
        )
        assert done.returncode == 2 and "git" in done.stderr and "Traceback" not in done.stderr, done


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
